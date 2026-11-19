package main // this is a standalone program; run with: go run prove.go
// Ask IPRX to prove a digest on Verae (original first-wins stamp, plus restamp history).
// Usage: go run prove.go [sha256]

import (
	"bytes"    // wrap the JSON body as an io.Reader
	"fmt"      // print the JSON
	"io"       // read the response body
	"net/http" // HTTP client
	"os"       // arguments and IPRX_BASE
)

func main() { // program entry point
	base := "https://iprx.org" // default API origin
	if v := os.Getenv("IPRX_BASE"); v != "" { // set IPRX_BASE only if you use a different host
		base = v
	}
	hash := "2c7606c0d53d7a800192f11609c939e66826f2af9c93fc971b850a97d5937466" // 192.0.2.1 add event
	if len(os.Args) > 1 { // the user passed a digest
		hash = os.Args[1]
	}
	payload := []byte(`{"digest":"` + hash + `"}`) // body may use digest or hash_id
	resp, err := http.Post(base+"/api/v1/prove", "application/json", bytes.NewReader(payload))
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
	fmt.Printf("%s\n", body) // may be prove.ok=false if the prover is down
}
