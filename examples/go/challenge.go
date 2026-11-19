package main // this is a standalone program; run with: go run challenge.go
// Fetch a SHA-256 proof-of-work challenge used by nomination and removal POSTs.
// Usage: go run challenge.go

import (
	"fmt"      // print the JSON
	"io"       // read the response body
	"net/http" // HTTP client
	"os"       // IPRX_BASE
)

func main() { // program entry point
	base := "https://iprx.org"                        // default API origin
	if v := os.Getenv("IPRX_BASE"); v != "" {         // set IPRX_BASE only if you use a different host
		base = v                                      // override
	}
	resp, err := http.Get(base + "/api/v1/challenge") // GET /api/v1/challenge
	if err != nil {                                   // transport error
		fmt.Fprintln(os.Stderr, err)                  // show it
		os.Exit(1)                                    // non-zero status
	}
	defer resp.Body.Close()                           // free the connection
	body, err := io.ReadAll(resp.Body)                // read every byte
	if err != nil {                                   // read error
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Printf("%s\n", body)                          // print {challenge, bits, expires_in}
}
