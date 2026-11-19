package main // this is a standalone program; run with: go run check.go
// Check whether one IPv4 address is listed, and why.
// Usage: go run check.go [ipv4]
// The response includes nomination_progress, for example "3/5".

import (
	"fmt"      // print the JSON
	"io"       // read the response body
	"net/http" // HTTP client from the standard library
	"os"       // command-line arguments and IPRX_BASE
)

func main() { // program entry point
	base := getenv("IPRX_BASE", "https://iprx.org")        // set IPRX_BASE only if you use a different host
	ip := arg(1, "192.0.2.1")                              // first argument, or TEST-NET-1
	resp, err := http.Get(base + "/api/v1/check/" + ip)    // GET /api/v1/check/{ip}
	must(err)                                              // stop on a transport error
	defer resp.Body.Close()                                // free the connection
	body, err := io.ReadAll(resp.Body)                     // read every byte
	must(err)                                              // stop on a read error
	fmt.Printf("%s\n", body)                               // print the JSON as received
}

func getenv(k, def string) string { // helper: environment variable with a default
	if v := os.Getenv(k); v != "" { // a non-empty value wins
		return v
	}
	return def // fall back
}

func arg(i int, def string) string { // helper: 1-based argv with a default
	if len(os.Args) > i { // the user passed this argument
		return os.Args[i]
	}
	return def // fall back
}

func must(err error) { // helper: exit on the first error
	if err != nil { // something failed
		fmt.Fprintln(os.Stderr, err) // show it
		os.Exit(1)                   // non-zero status
	}
}
