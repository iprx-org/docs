#!/usr/bin/env node
// Nominate every public IPv4 address in a local block file via the IPRX API.
// Usage: node submit_blockfile.mjs --dry-run ../samples/fail2ban.log
//
// This Node entry point runs the documented Python submitter so every supported
// format is parsed the same way (fail2ban, ipset, iptables, nftables, CrowdSec,
// CSV, hosts.deny, Apache/nginx, DROP-style lists, and plain IP/CIDR lists).
// Pass the same flags as python3 submit_blockfile.py — they are forwarded unchanged.
//
// One submitter email counts as one nominator toward the 5-distinct-nominator
// listing threshold, no matter how many IPs are in the file. This script does
// not send email. Private, reserved, and documentation addresses are skipped
// unless you pass --submit-documentation (TEST ONLY; the API returns HTTP 400).

import { spawn } from "node:child_process";           // run the Python submitter
import { fileURLToPath } from "node:url";             // this file's path
import { dirname, join } from "node:path";            // resolve ../python/submit_blockfile.py

const here = dirname(fileURLToPath(import.meta.url)); // directory of this script
const py = join(here, "..", "python", "submit_blockfile.py"); // the reference submitter
const child = spawn("python3", [py, ...process.argv.slice(2)], { stdio: "inherit" }); // forward every flag and all stdio
child.on("exit", (code, signal) => {                  // when the submitter finishes
  if (signal) process.kill(process.pid, signal);      // propagate a fatal signal
  process.exit(code ?? 1);                            // propagate the exit status
});
child.on("error", (err) => {                          // python3 missing, or the script is not there
  console.error(err.message);                         // show the error
  console.error(`expected the reference submitter at ${py}`); // where we looked
  process.exit(1);                                    // stop
});
