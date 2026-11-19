package main // this is a standalone program; run with: go run submit_blockfile.go --dry-run ../samples/fail2ban.log
// Nominate every public IPv4 address in a local block file via the IPRX API.
//
// This Go entry point runs the documented Python submitter so every supported
// format is parsed the same way (fail2ban, ipset, iptables, nftables, CrowdSec,
// CSV, hosts.deny, Apache/nginx, DROP-style lists, and plain IP/CIDR lists).
// Pass the same flags as python3 submit_blockfile.py — they are forwarded unchanged.
//
// One submitter email counts as one nominator toward the 5-distinct-nominator
// listing threshold, no matter how many IPs are in the file. This program does
// not send email. Private, reserved, and documentation addresses are skipped
// unless you pass --submit-documentation (TEST ONLY; the API returns HTTP 400).

import (
	"fmt"           // print errors
	"os"            // arguments and exit status
	"os/exec"       // run the Python submitter
	"path/filepath" // resolve ../python/submit_blockfile.py
	"runtime"       // this source file's path
)

func main() { // program entry point
	_, file, _, ok := runtime.Caller(0) // path of this .go file when it was compiled or run
	if !ok { // should not happen
		fmt.Fprintln(os.Stderr, "cannot resolve this source file")
		os.Exit(1)
	}
	py := filepath.Join(filepath.Dir(file), "..", "python", "submit_blockfile.py") // the reference submitter
	args := append([]string{py}, os.Args[1:]...) // python3 script.go-flags...
	cmd := exec.Command("python3", args...) // run the documented Python tool
	cmd.Stdin = os.Stdin   // forward stdin (not usually used)
	cmd.Stdout = os.Stdout // forward parsed rows and results
	cmd.Stderr = os.Stderr // forward format summaries and warnings
	if err := cmd.Run(); err != nil { // non-zero exit or a missing python3
		if ee, ok := err.(*exec.ExitError); ok { // the submitter itself failed
			os.Exit(ee.ExitCode()) // propagate its status
		}
		fmt.Fprintln(os.Stderr, err) // python3 missing, or the script is not there
		fmt.Fprintln(os.Stderr, "expected the reference submitter at", py)
		os.Exit(1)
	}
}
