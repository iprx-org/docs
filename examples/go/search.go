package main // this is a standalone program; run with: go run search.go
// Search public, redacted records by hostname, IP, hash_id, ASN, ISP, or country.
// Usage: go run search.go [query]

import (
	"fmt"      // print the JSON
	"io"       // read the response body
	"net/http" // HTTP client
	"net/url"  // encode the q parameter
	"os"       // arguments and IPRX_BASE
)

func main() { // program entry point
	base := getenv("IPRX_BASE", "https://iprx.org")                    // set IPRX_BASE only if you use a different host
	q := arg(1, "nt-isp")                                              // hostname substring or other public search term
	resp, err := http.Get(base + "/api/v1/search?q=" + url.QueryEscape(q)) // GET /api/v1/search?q=
	must(err)                                                          // stop on a transport error
	defer resp.Body.Close()                                            // free the connection
	body, err := io.ReadAll(resp.Body)                                 // read every byte
	must(err)                                                          // stop on a read error
	fmt.Printf("%s\n", body)                                           // print the JSON as received
}

func getenv(k, def string) string { // helper: environment variable with a default
	if v := os.Getenv(k); v != "" {
		return v
	}
	return def
}

func arg(i int, def string) string { // helper: 1-based argv with a default
	if len(os.Args) > i {
		return os.Args[i]
	}
	return def
}

func must(err error) { // helper: exit on the first error
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
