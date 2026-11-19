package main // this is a standalone program; run with: go run dkim_status.go
// Check the DKIM verification status of a removal request.
// Usage: go run dkim_status.go <event_id>

import (
	"fmt"      // print the JSON
	"io"       // read the response body
	"net/http" // HTTP client
	"os"       // arguments and IPRX_BASE
)

func main() { // program entry point
	if len(os.Args) < 2 { // event_id is required
		fmt.Fprintln(os.Stderr, "usage: go run dkim_status.go <event_id>") // how to run it
		os.Exit(2)
	}
	base := "https://iprx.org" // default API origin
	if v := os.Getenv("IPRX_BASE"); v != "" { // set IPRX_BASE only if you use a different host
		base = v
	}
	resp, err := http.Get(base + "/api/v1/removals/" + os.Args[1] + "/dkim-status") // GET the status document
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Printf("%s\n", body) // dkim_status is pending, passed, or failed
}
