# Sample block files

These files are **examples only**. Every routable address in them is from RFC 5737 documentation ranges:

- `192.0.2.0/24` (TEST-NET-1)
- `198.51.100.0/24` (TEST-NET-2)
- `203.0.113.0/24` (TEST-NET-3)

A few RFC 1918 / loopback addresses (`10.0.0.0/8`, `192.168.0.0/16`, `127.0.0.1`) are included on purpose so you can see the submitters skip them.

The IPRX nomination API rejects private, reserved, and documentation addresses. A `--dry-run` against these samples shows what would be parsed, skipped, and (for a real public IP) submitted. A live POST of a TEST-NET address returns HTTP 400.

| File | Format |
| --- | --- |
| `fail2ban-status.txt` | `fail2ban-client status <jail>` text |
| `fail2ban-banned.json` | `fail2ban-client banned` JSON |
| `fail2ban.log` | fail2ban log lines containing `Ban x.x.x.x` |
| `iplist.txt` | one IPv4 address per line |
| `cidr.txt` | one IPv4 CIDR per line |
| `nominations.csv` | CSV with `ip,reason` |
| `ipset.save` | `ipset save` |
| `iptables-save.txt` | `iptables-save` |
| `nftables.conf` | nftables set dump |
| `crowdsec-decisions.json` | `cscli decisions list -o json` |
| `hosts.deny` | `/etc/hosts.deny` / DenyHosts |
| `apache-deny.conf` | Apache `Require not ip` / `Deny from` |
| `nginx-deny.conf` | nginx `deny` directives |
| `spamhaus-drop.txt` | `ip ; comment` (DROP style) |

See [../README.md](../README.md) and [../../scripts.md](../../scripts.md) for how to run the submitters.
