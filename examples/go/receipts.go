package main // this is a standalone program; run with: go run receipts.go
// Download one event receipt as JSON, HTML, and PDF, plus the whole-IP bundle.
// Usage: go run receipts.go [hash_id_or_event_id] [ipv4] [outdir]

import (
	"fmt"           // log each download
	"io"            // copy the response body
	"net/http"      // HTTP client
	"os"            // arguments, IPRX_BASE, file writes
	"path/filepath" // join the output directory and file name
)

func main() { // program entry point
	base := getenv("IPRX_BASE", "https://iprx.org") // set IPRX_BASE only if you use a different host
	key := arg(1, "2c7606c0d53d7a800192f11609c939e66826f2af9c93fc971b850a97d5937466") // 192.0.2.1 add event
	ip := arg(2, "192.0.2.1")                     // address for the bundle
	out := arg(3, "/tmp/iprx-receipts")           // where to save the files
	must(os.MkdirAll(out, 0o755))                 // create the folder if needed
	fetch(base+"/api/v1/receipts/"+key+".json", filepath.Join(out, "receipt.json")) // canonical JSON
	fetch(base+"/api/v1/receipts/"+key+".html", filepath.Join(out, "receipt.html")) // printable HTML
	fetch(base+"/api/v1/receipts/"+key+".pdf", filepath.Join(out, "receipt.pdf"))   // PDF
	fetch(base+"/api/v1/receipts/ip/"+ip+".json", filepath.Join(out, "bundle.json")) // whole-IP bundle
}

func fetch(url, dest string) { // GET a URL to a local file
	resp, err := http.Get(url) // download
	must(err)                  // stop on a transport error
	defer resp.Body.Close()    // free the connection
	if resp.StatusCode != 200 { // unexpected status
		must(fmt.Errorf("HTTP %d for %s", resp.StatusCode, url)) // fail loudly
	}
	f, err := os.Create(dest) // create or replace the file
	must(err)                 // stop on a file error
	defer f.Close()           // flush and close
	n, err := io.Copy(f, resp.Body) // write every byte (PDF is binary)
	must(err)                 // stop on a write error
	fmt.Printf("%s: %d bytes\n", dest, n) // confirm it landed
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
