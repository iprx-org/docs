#!/usr/bin/env python3
# Submit every IPv4 address in a local block file as an IPRX nomination.
# Usage:
#   python3 submit_blockfile.py --dry-run ../samples/fail2ban.log
#   python3 submit_blockfile.py --limit 3 --reason "lab sensor ban" --email you@example.org --name "Your Name" bans.txt
#   python3 submit_blockfile.py --token "$IPRX_TOKEN" --email you@example.org --name "Your Name" bans.txt
# Every nomination uses your verified email (and the client IP the API sees) as one nominator.
# Five distinct nominators are required before IPRX auto-lists an address; a bulk
# file from one person still counts as a single nominator for each IP, not five.
# Documentation, reserved, and private addresses are skipped (and rejected by the API).
# Anonymous submissions are capped at 10 an hour and must solve a proof-of-work.
# A verified token (--token or IPRX_TOKEN) skips the proof-of-work and has no rate limit.

from __future__ import annotations  # allow modern type hints on older Python

import argparse  # parse --dry-run, --limit, --reason, and the other flags
import csv  # read the ip,reason CSV format
import hashlib  # SHA-256 for the proof-of-work and for hashing nothing else
import ipaddress  # validate IPv4 addresses and expand CIDR prefixes
import json  # parse JSON inputs and write the results JSONL
import os  # read IPRX_BASE from the environment
import re  # pull IPv4 addresses out of free-form log and config lines
import sys  # print errors to stderr and set the exit status
import time  # sleep between submissions so we stay under the rate limit
import urllib.error  # catch HTTP 4xx/5xx from the API
import urllib.request  # stdlib HTTP client; no third-party packages required
from typing import Any  # JSON-shaped values in parse results

BASE_DEFAULT = "https://iprx.org"  # change with --base or IPRX_BASE
IPV4_RE = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\b")  # dotted IPv4
CIDR_RE = re.compile(IPV4_RE.pattern + r"/(?:3[0-2]|[12]?\d)")  # dotted IPv4 plus a prefix length
BAN_RE = re.compile(r"\bBan\s+(\d{1,3}(?:\.\d{1,3}){3})\b", re.IGNORECASE)  # fail2ban "Ban x.x.x.x"
DOC_NETS = [  # RFC 5737 TEST-NET ranges; Python 3.13 dropped is_documentation
    ipaddress.ip_network("192.0.2.0/24"),  # TEST-NET-1
    ipaddress.ip_network("198.51.100.0/24"),  # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),  # TEST-NET-3
]

def is_skippable(addr: ipaddress.IPv4Address) -> str | None:  # define is_skippable()
    # Return a short reason if this address must not be nominated, else None.
    if any(addr in n for n in DOC_NETS):  # check TEST-NET before is_private (3.13 treats them as private)
        return "documentation (TEST-NET)"  # return the result
    if addr.is_loopback or addr.is_link_local or addr.is_multicast:  # 127/8, 169.254/16, 224/4
        return "non-global"  # return the result
    if addr.is_unspecified:  # 0.0.0.0
        return "reserved"  # return the result
    if addr.is_private:  # RFC 1918, including 10/8, 172.16/12, 192.168/16
        return "private"  # return the result
    if addr.is_reserved:  # other IANA reserved space
        return "reserved"  # return the result
    return None  # appears to be a regular public IPv4 address

def parse_ip(text: str) -> tuple[str, str | None] | None:  # define parse_ip()
    # Parse one IPv4 host and say whether it should be skipped.
    try:  # ipaddress raises ValueError on junk
        addr = ipaddress.ip_address(text.strip())  # accept "192.0.2.10"
    except ValueError:  # the text was not an IP or prefix
        return None  # not an IP
    if not isinstance(addr, ipaddress.IPv4Address):  # ignore IPv6
        return None  # caller should ignore this value
    return str(addr), is_skippable(addr)  # canonical dotted quad plus skip reason

def expand_cidr(text: str, max_hosts: int) -> tuple[list[str], str | None]:  # define expand_cidr()
    # Expand a CIDR to host addresses, or return a skip reason for the whole prefix.
    try:  # try the next statement
        net = ipaddress.ip_network(text.strip(), strict=False)  # accept host bits in the address
    except ValueError:  # the text was not an IP or prefix
        return [], "invalid CIDR"  # [], "invalid CIDR" — nothing expanded
    if not isinstance(net, ipaddress.IPv4Network):  # ignore IPv6
        return [], "not IPv4"  # [], "not IPv4" — nothing expanded
    if net.prefixlen < 32:  # a real prefix, not a single host
        r0 = is_skippable(net.network_address)  # reason at the first address
        r1 = is_skippable(net.broadcast_address)  # reason at the last address
        if r0 and r0 == r1 and r0 == "private":  # both ends are RFC 1918 (or similar private)
            return [], f"private prefix ({net})"  # one skip for the whole range
        if r0 and r0 == r1 and r0 == "non-global":  # loopback / link-local / multicast
            return [], f"non-global prefix ({net})"  # one skip for the whole range
    if net.num_addresses > max_hosts:  # compare the full prefix size, including network/broadcast
        return [], f"prefix too large ({net.num_addresses} addresses; raise --max-cidr-size to expand)"  # skip oversized prefixes
    hosts = list(net)  # include network and broadcast; blocklists often mean the whole prefix
    return [str(h) for h in hosts], None  # dotted quads

def add_item(out: list[dict[str, Any]], seen: set[str], ip: str, reason: str | None, source: str) -> None:  # define add_item()
    # Append a unique address with the best reason we have so far.
    parsed = parse_ip(ip)  # validate
    if not parsed:  # skip junk
        return  # see the flag or value on this line
    ip, skip = parsed  # unpack
    if ip in seen:  # already queued from an earlier line
        return  # see the flag or value on this line
    seen.add(ip)  # remember it
    out.append({"ip": ip, "reason": reason, "skip": skip, "source": source})  # one result row

# define add_cidr_or_ip()
def add_cidr_or_ip(out: list[dict[str, Any]], seen: set[str], token: str, reason: str | None, source: str, max_hosts: int) -> None:  # accept a host or a CIDR
    # Accept either a host or a CIDR token.
    token = token.strip().rstrip(";")  # nginx lines end with a semicolon
    if "/" in token:  # looks like a prefix
        hosts, err = expand_cidr(token, max_hosts)  # expand or skip
        if err:  # too large or invalid
            if token not in seen:  # record the prefix once
                seen.add(token)  # remember this address so we do not add it twice
                out.append({"ip": token, "reason": reason, "skip": err, "source": source})  # keep this parsed address
            return  # see the flag or value on this line
        for host in hosts:  # each expanded address
            add_item(out, seen, host, reason, source)  # record or recurse on this value
        return  # see the flag or value on this line
    add_item(out, seen, token, reason, source)  # plain host

def detect_format(text: str, forced: str | None) -> str:  # define detect_format()
    # Guess the input format, or honour --format.
    if forced and forced != "auto":  # caller already knows
        return forced  # return the result
    stripped = text.lstrip()  # ignore a leading BOM or blank line
    if stripped.startswith("{") or stripped.startswith("["):  # JSON
        return "json"  # return the result
    if "Status for the jail:" in text and "Banned IP list:" in text:  # fail2ban-client status
        return "fail2ban-status"  # return the result
    if re.search(r"fail2ban\.\w+.*\bBan\s+\d", text):  # fail2ban.log
        return "fail2ban-log"  # return the result
    if re.search(r"^create\s+\S+", text, re.M) and re.search(r"^add\s+\S+", text, re.M):  # ipset save
        return "ipset"  # return the result
    if re.search(r"^\*filter\b", text, re.M) or re.search(r"^-A\s+\S+\s+-s\s+", text, re.M):  # iptables-save
        return "iptables"  # return the result
    if "elements = {" in text or "type ipv4_addr" in text:  # nftables set
        return "nftables"  # return the result
    if re.search(r"(?i)^\s*deny\s+\d", text, re.M) and "Require not ip" not in text:  # nginx deny
        return "nginx"  # return the result
    if re.search(r"(?i)Require not ip\s+|^\s*Deny from\s+", text, re.M):  # Apache
        return "apache"  # return the result
    if re.search(r"(?i)^\s*(sshd|ALL|in\.smtpd|vsftpd)\s*:", text, re.M):  # hosts.deny
        return "hosts.deny"  # return the result
    if re.search(r"^\s*\d{1,3}(?:\.\d{1,3}){3}(?:/\d{1,2})?\s*;", text, re.M):  # Spamhaus DROP
        return "spamhaus"  # return the result
    first = next((ln for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")), "")  # first data line
    if "," in first and re.search(r"(?i)\bip\b", first.split(",")[0] if "ip" in first.lower().split(",")[0:2] else first):  # rough CSV header
        return "csv"  # return the result
    if first.lower().startswith("ip,") or first.lower().startswith("ip;"):  # typical header
        return "csv"  # return the result
    return "list"  # plain IP / CIDR list, or a generic extract

# define parse_json_blob()
def parse_json_blob(data: Any, out: list[dict[str, Any]], seen: set[str], default_reason: str, max_hosts: int) -> None:  # CrowdSec, fail2ban banned, or nested JSON
    # CrowdSec decisions list, or fail2ban-client banned JSON, or a generic list of IPs.
    if isinstance(data, list):  # a JSON array
        for item in data:  # each element
            parse_json_blob(item, out, seen, default_reason, max_hosts)  # record or recurse on this value
        return  # see the flag or value on this line
    if isinstance(data, str):  # a lone IP string
        add_cidr_or_ip(out, seen, data, default_reason, "json", max_hosts)  # record or recurse on this value
        return  # see the flag or value on this line
    if not isinstance(data, dict):  # numbers / null
        return  # see the flag or value on this line
    # CrowdSec decision objects have scope/value (and usually a reason/scenario).
    scope = str(data.get("scope") or "")  # "Ip" or "Range"
    value = data.get("value") or data.get("ip")  # CrowdSec uses "value"
    reason = data.get("reason") or data.get("scenario") or default_reason  # prefer the decision reason
    if value and scope.lower() in {"", "ip", "range", "ipv4"}:  # a decision row
        add_cidr_or_ip(out, seen, str(value), str(reason), "crowdsec", max_hosts)  # record or recurse on this value
        return  # see the flag or value on this line
    # fail2ban-client banned: [ {"sshd": ["1.2.3.4", ...]}, ... ] or {"sshd": [...]}
    for key, val in data.items():  # each jail or field
        # branch: if key.lower() in {"scope", "value", "ip", "reason", "scenario", "duration", "type", "origin", "id"}
        if key.lower() in {"scope", "value", "ip", "reason", "scenario", "duration", "type", "origin", "id"}:  # skip CrowdSec metadata keys
            continue  # already handled as a decision, or not an IP list
        if isinstance(val, list):  # a jail's banned list
            for item in val:  # loop: for item in val
                if isinstance(item, str):  # branch: if isinstance(item, str)
                    # record or recurse on this value
                    add_cidr_or_ip(out, seen, item, default_reason or f"fail2ban jail {key}", "fail2ban-banned", max_hosts)  # one banned address in that jail
                else:  # see the flag or value on this line
                    parse_json_blob(item, out, seen, default_reason, max_hosts)  # record or recurse on this value
        elif isinstance(val, str) and IPV4_RE.search(val):  # a single IP field
            add_cidr_or_ip(out, seen, val, default_reason, "json", max_hosts)  # record or recurse on this value

def parse_text(text: str, fmt: str, default_reason: str, max_hosts: int) -> list[dict[str, Any]]:  # define parse_text()
    # Turn a whole file into a de-duplicated list of {ip, reason, skip, source}.
    out: list[dict[str, Any]] = []  # results in file order
    seen: set[str] = set()  # de-dupe key
    if fmt == "json":  # CrowdSec or fail2ban banned
        parse_json_blob(json.loads(text), out, seen, default_reason, max_hosts)  # record or recurse on this value
        return out  # return the result
    if fmt == "csv":  # ip,reason with a header row
        reader = csv.DictReader(line for line in text.splitlines() if line.strip())  # skip blanks
        for row in reader:  # each record
            ip = (row.get("ip") or row.get("IP") or row.get("address") or "").strip()  # column name
            reason = (row.get("reason") or row.get("Reason") or row.get("comment") or default_reason)  # per-line reason
            if ip:  # branch: if ip
                add_cidr_or_ip(out, seen, ip, reason, "csv", max_hosts)  # record or recurse on this value
        return out  # return the result
    if fmt == "fail2ban-status":  # look for "Banned IP list:"
        for line in text.splitlines():  # loop: for line in text.splitlines()
            if "Banned IP list:" in line:  # the only line we need
                _, _, rest = line.partition("Banned IP list:")  # IPs follow the label
                for tok in rest.replace("`", " ").split():  # split on whitespace
                    add_item(out, seen, tok, default_reason, "fail2ban-status")  # record or recurse on this value
        return out  # return the result
    if fmt == "fail2ban-log":  # NOTICE [sshd] Ban 192.0.2.10
        for line in text.splitlines():  # loop: for line in text.splitlines()
            m = BAN_RE.search(line)  # only "Ban", not "Unban"
            if m:  # branch: if m
                add_item(out, seen, m.group(1), default_reason, "fail2ban-log")  # record or recurse on this value
        return out  # return the result
    if fmt == "ipset":  # "add <set> <ip> [comment ...]"
        for line in text.splitlines():  # loop: for line in text.splitlines()
            s = line.strip()  # local variable used in the next steps
            if not s.startswith("add "):  # ignore "create" lines
                continue  # move on to the next item
            parts = s.split()  # add name ip ...
            if len(parts) >= 3:  # branch: if len(parts) >= 3
                reason = default_reason  # fall back to --reason
                if "comment" in parts:  # ipset comment is the rest of the line
                    # local variable used in the next steps
                    reason = " ".join(parts[parts.index("comment") + 1 :]).strip('"') or default_reason  # ipset comment becomes the reason
                add_cidr_or_ip(out, seen, parts[2], reason, "ipset", max_hosts)  # record or recurse on this value
        return out  # return the result
    if fmt == "iptables":  # -A CHAIN -s 192.0.2.10/32 -j DROP
        for line in text.splitlines():  # loop: for line in text.splitlines()
            m = re.search(r"-s\s+(\d{1,3}(?:\.\d{1,3}){3}(?:/\d{1,2})?)", line)  # the -s address
            if m and re.search(r"-j\s+(DROP|REJECT|BAN)\b", line, re.I):  # only drop/reject/ban rules
                add_cidr_or_ip(out, seen, m.group(1), default_reason, "iptables", max_hosts)  # record or recurse on this value
        return out  # return the result
    if fmt == "nftables":  # elements = { 192.0.2.10, 192.0.2.11 }
        for block in re.findall(r"elements\s*=\s*\{([^}]*)\}", text, re.S):  # each set's members
            for tok in block.replace("\n", " ").split(","):  # comma-separated
                tok = tok.strip()  # see the flag or value on this line
                if tok:  # branch: if tok
                    add_cidr_or_ip(out, seen, tok, default_reason, "nftables", max_hosts)  # record or recurse on this value
        # Also pick up "ip saddr 192.0.2.10 drop" rules that are not in a set.
        # loop: for m in re.finditer(r"ip\s+saddr\s+(\d{1,3}(?:\.\d{1,3}){3}(?:/\d{1,2})?)", text)
        for m in re.finditer(r"ip\s+saddr\s+(\d{1,3}(?:\.\d{1,3}){3}(?:/\d{1,2})?)", text):  # also collect lone ip saddr drop rules
            add_cidr_or_ip(out, seen, m.group(1), default_reason, "nftables", max_hosts)  # record or recurse on this value
        return out  # return the result
    if fmt == "nginx":  # deny 192.0.2.10;
        for line in text.splitlines():  # loop: for line in text.splitlines()
            m = re.search(r"(?i)^\s*deny\s+(\S+?);", line)  # local variable used in the next steps
            if m:  # branch: if m
                add_cidr_or_ip(out, seen, m.group(1), default_reason, "nginx", max_hosts)  # record or recurse on this value
        return out  # return the result
    if fmt == "apache":  # Require not ip 192.0.2.10   /   Deny from 192.0.2.10
        for line in text.splitlines():  # loop: for line in text.splitlines()
            m = re.search(r"(?i)(?:Require not ip|Deny from)\s+(\S+)", line)  # local variable used in the next steps
            if m:  # branch: if m
                add_cidr_or_ip(out, seen, m.group(1), default_reason, "apache", max_hosts)  # record or recurse on this value
        return out  # return the result
    if fmt == "hosts.deny":  # sshd: 192.0.2.10 192.0.2.11
        for line in text.splitlines():  # loop: for line in text.splitlines()
            s = line.strip()  # local variable used in the next steps
            if not s or s.startswith("#"):  # comments
                continue  # move on to the next item
            if ":" not in s:  # not a wrappers line
                continue  # move on to the next item
            _, _, rest = s.partition(":")  # clients after the daemon name
            for tok in rest.replace(",", " ").split():  # loop: for tok in rest.replace(",", " ").split()
                if tok.startswith("#"):  # inline comment
                    break  # stop scanning this line
                add_cidr_or_ip(out, seen, tok, default_reason, "hosts.deny", max_hosts)  # record or recurse on this value
        return out  # return the result
    if fmt == "spamhaus":  # 192.0.2.0/24 ; SBL123
        for line in text.splitlines():  # loop: for line in text.splitlines()
            s = line.strip()  # local variable used in the next steps
            if not s or s.startswith(";") or s.startswith("#"):  # comments use ;
                continue  # move on to the next item
            if ";" in s:  # branch: if ";" in s
                cidr, _, comment = s.partition(";")  # reason after the semicolon
                # record or recurse on this value
                add_cidr_or_ip(out, seen, cidr.strip(), comment.strip() or default_reason, "spamhaus", max_hosts)  # prefix plus the DROP comment
            else:  # see the flag or value on this line
                add_cidr_or_ip(out, seen, s, default_reason, "spamhaus", max_hosts)  # record or recurse on this value
        return out  # return the result
    # Plain list, or unknown text: one IP/CIDR per line, optional "reason" after whitespace or #.
    for line in text.splitlines():  # loop: for line in text.splitlines()
        s = line.strip()  # local variable used in the next steps
        if not s or s.startswith("#") or s.startswith(";"):  # comments
            continue  # move on to the next item
        if s.lower().startswith("ip,") or s.lower() == "ip":  # stray CSV header
            continue  # move on to the next item
        token = s.split()[0].rstrip(",")  # first field
        rest = s[len(s.split()[0]) :].strip().lstrip("#").strip()  # leftover as a reason
        reason = rest or default_reason  # local variable used in the next steps
        add_cidr_or_ip(out, seen, token, reason, "list", max_hosts)  # record or recurse on this value
    return out  # return the result

def leading_zero_bits(digest: bytes) -> int:  # define leading_zero_bits()
    # Count how many leading zero bits a SHA-256 digest starts with.
    zeros = 0  # running total
    for b in digest:  # each byte, left to right
        if b == 0:  # a zero byte is eight zero bits
            zeros += 8  # see the flag or value on this line
            continue  # move on to the next item
        zeros += 8 - b.bit_length()  # 0b0001.... has 3 leading zeros
        break  # stop scanning this line
    return zeros  # return the result

def solve_pow(challenge: str, bits: int) -> str:  # define solve_pow()
    # Find a nonce so SHA-256(challenge + ":" + nonce) has `bits` leading zero bits.
    prefix = f"{challenge}:"  # the API hashes this exact string
    nonce = 0  # start from zero; any unique string would work
    while True:  # 18 bits is typically under a million tries, usually a second or so
        n = str(nonce)  # local variable used in the next steps
        digest = hashlib.sha256((prefix + n).encode("utf-8")).digest()  # local variable used in the next steps
        if leading_zero_bits(digest) >= bits:  # hard enough
            return n  # return the result
        nonce += 1  # see the flag or value on this line

def http_json(method: str, url: str, body: dict[str, Any] | None = None, timeout: int = 30, token: str | None = None) -> tuple[int, Any]:  # define http_json()
    # GET or POST JSON and return (status, parsed body).
    data = None if body is None else json.dumps(body).encode("utf-8")  # encode the object
    headers = {"Accept": "application/json", "User-Agent": "iprx-docs-examples/1.0"}  # identify this script
    if data is not None:  # branch: if data is not None
        headers["Content-Type"] = "application/json"  # the nominations API expects JSON
    if token:  # a verified API token skips the proof-of-work and the anonymous rate limit
        headers["Authorization"] = f"Bearer {token}"  # format: Authorization: Bearer iprx_…
    req = urllib.request.Request(url, data=data, headers=headers, method=method)  # local variable used in the next steps
    try:  # try the next statement
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # follow the request
            raw = resp.read()  # local variable used in the next steps
            return resp.status, (json.loads(raw) if raw else {})  # return the result
    except urllib.error.HTTPError as exc:  # 4xx / 5xx still have a body
        raw = exc.read()  # local variable used in the next steps
        try:  # try the next statement
            parsed = json.loads(raw) if raw else {}  # local variable used in the next steps
        except json.JSONDecodeError:  # body was not JSON; keep the raw text
            parsed = {"raw": raw.decode("utf-8", "replace")}  # local variable used in the next steps
        return exc.code, parsed  # return the result

def submit_one(base: str, item: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:  # define submit_one()
    # POST one nomination. With --token / IPRX_TOKEN, skip the proof-of-work.
    reason = item.get("reason") or args.reason  # per-line reason wins, then --reason
    body = {  # the NominationIn schema
        "ip": item["ip"],  # see the flag or value on this line
        "reason": reason,  # see the flag or value on this line
        "evidence": args.evidence,  # optional supporting text
        "name": args.name,  # who is nominating
        "email": args.email,  # required by the API; also used to count distinct nominators
        "org": args.org,  # optional organisation
        "company_url": "",  # honeypot; must stay empty or the API rejects the request
    }  # see the flag or value on this line
    token = (args.token or "").strip() or None  # Bearer token, if the user supplied one
    if not token:  # anonymous path still needs a challenge and a proof-of-work
        status, challenge = http_json("GET", f"{base}/api/v1/challenge")  # start a new proof-of-work
        if status != 200 or not isinstance(challenge, dict) or "challenge" not in challenge:  # challenge endpoint must succeed
            return {"ip": item["ip"], "ok": False, "http_status": status, "error": challenge}  # cannot continue
        nonce = solve_pow(str(challenge["challenge"]), int(challenge.get("bits") or 18))  # usually 18 bits
        body["challenge"] = challenge["challenge"]  # opaque string from GET /challenge
        body["pow_nonce"] = nonce  # the nonce we just found
    status, resp = http_json("POST", f"{base}/api/v1/nominations", body, token=token)  # 201 on success
    row = {  # one results-JSONL object
        "ip": item["ip"],  # see the flag or value on this line
        "ok": status == 201,  # see the flag or value on this line
        "http_status": status,  # see the flag or value on this line
        "reason": reason,  # see the flag or value on this line
        "response": resp,  # see the flag or value on this line
    }  # see the flag or value on this line
    if isinstance(resp, dict):  # pull the useful fields up top
        row["event_id"] = resp.get("event_id")  # see the flag or value on this line
        row["hash_id"] = resp.get("hash_id")  # see the flag or value on this line
        hid = resp.get("hash_id") or resp.get("event_id")  # local variable used in the next steps
        if hid:  # public receipt URL
            row["receipt_url"] = f"{base}/api/v1/receipts/{hid}.json"  # see the flag or value on this line
    return row  # return the result

def main() -> int:  # define main()
    parser = argparse.ArgumentParser(description="Nominate IPv4 addresses from a local block file via the IPRX API.")  # help text
    parser.add_argument("path", help="path to a fail2ban, ipset, iptables, nft, CrowdSec, CSV, or plain IP file")  # positional
    parser.add_argument("--format", default="auto", help="force a parser: auto, json, csv, list, fail2ban-status, fail2ban-log, fail2ban-banned, ipset, iptables, nftables, nginx, apache, hosts.deny, spamhaus, crowdsec")  # optional
    parser.add_argument("--reason", default="Nominated from a local block file via the IPRX examples submitter.", help="default reason when the file has none")  # required-quality text
    parser.add_argument("--evidence", default=None, help="optional evidence string sent with every nomination")  # optional
    parser.add_argument("--name", default=None, help="your display name (sent as the nominator)")  # identity
    parser.add_argument("--email", default=None, help="your email; required for a live submit so distinct nominators can be counted")  # identity
    parser.add_argument("--org", default=None, help="optional organisation name")  # identity
    parser.add_argument("--base", default=os.environ.get("IPRX_BASE", BASE_DEFAULT), help="API origin, default https://iprx.org")  # host
    parser.add_argument("--dry-run", action="store_true", help="parse and print, but do not call the API")  # safe mode
    parser.add_argument("--submit-documentation", action="store_true", help="TEST ONLY: also POST RFC 5737 TEST-NET addresses; the API rejects them with HTTP 400")  # used in docs tests
    parser.add_argument("--limit", type=int, default=0, help="nominate at most N eligible addresses (0 means no cap)")  # cap
    parser.add_argument("--max-cidr-size", type=int, default=256, help="refuse to expand a prefix larger than this many addresses (default 256 = /24)")  # safety
    parser.add_argument("--delay", type=float, default=None, help="seconds to wait between live submissions (default 1 without a token, 0 with a token)")  # pacing
    parser.add_argument("--token", default=os.environ.get("IPRX_TOKEN"), help="verified API token (or set IPRX_TOKEN); skips the proof-of-work and the anonymous 10/hour cap")  # auth
    parser.add_argument("--output", default="nomination-results.jsonl", help="where to append per-IP results as JSONL")  # results
    args = parser.parse_args()  # parse sys.argv
    if args.delay is None:  # pick a default based on whether a token is present
        args.delay = 0.0 if (args.token or "").strip() else 1.0  # token users have no rate limit
    path = args.path  # local file
    text = open(path, encoding="utf-8", errors="replace").read()  # load the whole file
    forced = None if args.format in {"auto", "fail2ban-banned", "crowdsec"} else args.format  # json covers those two
    if args.format in {"fail2ban-banned", "crowdsec"}:  # both are JSON
        forced = "json"  # local variable used in the next steps
    fmt = detect_format(text, forced)  # decide the parser
    items = parse_text(text, fmt, args.reason, args.max_cidr_size)  # de-duplicated rows
    print(f"# format={fmt} parsed={len(items)} file={path}", file=sys.stderr)  # summary on stderr
    if args.submit_documentation:  # keep TEST-NET rows so we can show the API's 400
        eligible = [it for it in items if (not it.get("skip")) or it.get("skip") == "documentation (TEST-NET)"]  # public + documentation
        skipped = [it for it in items if it.get("skip") and it.get("skip") != "documentation (TEST-NET)"]  # still skip private/reserved
    else:
        eligible = [it for it in items if not it.get("skip")]  # public IPs only
        skipped = [it for it in items if it.get("skip")]  # everything else
    if args.limit and args.limit > 0:  # honour --limit
        eligible = eligible[: args.limit]  # local variable used in the next steps
    for it in skipped:  # always show skips first
        # write this line to the user
        print(json.dumps({"ip": it["ip"], "action": "skip", "why": it["skip"], "source": it["source"]}, sort_keys=True))  # show every skipped address
    if args.dry_run:  # no HTTP writes
        for it in eligible:  # loop: for it in eligible
            # write this line to the user
            print(json.dumps({"ip": it["ip"], "action": "would-nominate", "reason": it.get("reason") or args.reason, "source": it["source"]}, sort_keys=True))  # show what a live run would send
        print(f"# dry-run complete: would nominate {len(eligible)}, skipped {len(skipped)}", file=sys.stderr)
        print("# note: one submitter email counts as one nominator toward the 5-distinct-nominator listing threshold", file=sys.stderr)
        return 0  # success
    if not args.email or not args.name:  # the API needs an identity for live posts
        print("live submit requires --email and --name (used to count distinct nominators)", file=sys.stderr)  # write this line to the user
        return 2  # missing required identity flags
    if not eligible:  # nothing to send
        print(f"# nothing to nominate ({len(skipped)} skipped)", file=sys.stderr)
        return 0  # success
    if (args.token or "").strip():  # verified token path
        print("# using IPRX_TOKEN / --token: proof-of-work skipped, no per-token nomination rate limit", file=sys.stderr)
    else:
        print("# anonymous path: 10 nominations per hour per client; 429s are retried", file=sys.stderr)
    written = 0  # successful 201s
    with open(args.output, "a", encoding="utf-8") as fh:  # append, so reruns keep history
        for i, it in enumerate(eligible):  # one POST each
            if i and args.delay > 0:  # pause between calls, not before the first
                time.sleep(args.delay)  # see the flag or value on this line
            row = submit_one(args.base.rstrip("/"), it, args)  # challenge + PoW + POST
            if row.get("http_status") == 429:  # rate-limited
                wait = 60  # default one minute
                print(f"# HTTP 429 for {it['ip']}; waiting {wait}s and retrying once", file=sys.stderr)
                time.sleep(wait)  # see the flag or value on this line
                row = submit_one(args.base.rstrip("/"), it, args)  # single retry
            fh.write(json.dumps(row, sort_keys=True) + "\n")  # results JSONL
            fh.flush()  # keep the file current if we stop early
            print(json.dumps({k: row[k] for k in row if k != "response"}, sort_keys=True))  # compact stdout
            if row.get("ok"):  # branch: if row.get("ok")
                written += 1  # see the flag or value on this line
    print(f"# finished: submitted_ok={written} attempted={len(eligible)} skipped={len(skipped)} results={args.output}", file=sys.stderr)
    print("# each of these nominations counts as the same single nominator toward the 5-distinct-nominator threshold", file=sys.stderr)
    return 0 if written == len(eligible) else 1  # non-zero if anything failed

if __name__ == "__main__":  # run when executed as a script
    sys.exit(main())  # propagate the exit code
