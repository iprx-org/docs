package main // this is a standalone program; run with: go run dkim_upload.go
// Upload a DKIM-signed .eml to prove domain control for a removal request.
// Usage: go run dkim_upload.go <event_id> <message.eml>
// This program only uploads a local file; it does not send any email.

import (
	"bytes"     // hold the multipart body
	"fmt"       // print status and errors
	"io"        // read the response
	"mime/multipart" // build the eml form field
	"net/http"  // HTTP client
	"os"        // arguments, IPRX_BASE, and the local .eml
)

func main() { // program entry point
	if len(os.Args) < 3 { // both arguments are required
		fmt.Fprintln(os.Stderr, "usage: go run dkim_upload.go <event_id> <message.eml>") // how to run it
		os.Exit(2) // usage error
	}
	eventID := os.Args[1] // from the removal response
	emlPath := os.Args[2] // path to a raw RFC822 .eml on disk
	raw, err := os.ReadFile(emlPath) // read the local file
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if len(raw) < 20 { // too small to be a real message
		fmt.Fprintln(os.Stderr, "eml file is empty or too short")
		os.Exit(1)
	}
	base := "https://iprx.org" // default API origin
	if v := os.Getenv("IPRX_BASE"); v != "" { // set IPRX_BASE only if you use a different host
		base = v
	}
	var buf bytes.Buffer // the multipart body
	w := multipart.NewWriter(&buf) // let the library pick a boundary
	part, err := w.CreateFormFile("eml", "message.eml") // field name is eml
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if _, err := part.Write(raw); err != nil { // write the .eml bytes
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := w.Close(); err != nil { // finish the body
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	req, err := http.NewRequest("POST", base+"/api/v1/removals/"+eventID+"/dkim", &buf) // upload the proof
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	req.Header.Set("Accept", "application/json") // ask for JSON
	req.Header.Set("Content-Type", w.FormDataContentType()) // includes the boundary
	resp, err := http.DefaultClient.Do(req) // send it
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body) // result is stamped either way
	fmt.Println(resp.StatusCode) // 201 when the check is recorded
	fmt.Println(string(body))
}
