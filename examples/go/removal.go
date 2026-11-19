package main // this is a standalone program; run with: go run removal.go
// Request removal of one IPv4 address: challenge, proof-of-work, POST /removals.
// Usage: go run removal.go [ipv4] [reason]
// Success is 201 with status pending_dkim and a one-time token.
// The token is saved under ~/.iprx/<event_id>.token with mode 600; do not commit it.
// This program does not send email.

import (
	"bytes"         // wrap the JSON body as an io.Reader
	"crypto/sha256" // SHA-256 for the proof-of-work
	"encoding/json" // request and response JSON
	"fmt"           // print status and errors
	"io"            // read the response body
	"net/http"      // HTTP client
	"os"            // arguments, environment, and the private token file
	"path/filepath" // ~/.iprx/<event_id>.token
	"strconv"       // convert the nonce counter to a string
)

func main() { // program entry point
	base := getenv("IPRX_BASE", "https://iprx.org")       // set IPRX_BASE only if you use a different host
	ip := arg(1, "192.0.2.1")                              // address to request removal for
	reason := arg(2, "TEST documentation removal request from the IPRX examples; not a real delist.") // >= 8 chars
	name := getenv("IPRX_NAME", "IPRX examples TEST")      // your display name
	email := getenv("IPRX_EMAIL", "docs-test@example.com") // an address you control
	ch := map[string]any{}                                 // {challenge, bits, expires_in}
	must(getJSON(base+"/api/v1/challenge", &ch))           // fetch a one-time challenge
	challenge, _ := ch["challenge"].(string)               // opaque string
	bits := 18                                             // default difficulty
	if v, ok := ch["bits"].(float64); ok {                 // JSON numbers decode as float64
		bits = int(v)                                      // use the server's value
	}
	nonce := solvePow(challenge, bits)                     // usually 18 leading zero bits
	body := map[string]any{                                // RemovalIn
		"ip":          ip,
		"name":        name,
		"email":       email,
		"reason":      reason,
		"org":         "IPRX docs examples",
		"challenge":   challenge,
		"pow_nonce":   nonce,
		"company_url": "", // honeypot; must stay empty
	}
	status, raw := postJSON(base+"/api/v1/removals", body) // 201 pending_dkim when healthy
	fmt.Println(status)                                    // HTTP status
	fmt.Println(string(raw))                               // body includes a token — keep it private
	var resp map[string]any                                // parse so we can save the token
	if json.Unmarshal(raw, &resp) == nil {                 // ignore non-JSON errors
		token, _ := resp["token"].(string)                 // one-time token
		eventID, _ := resp["event_id"].(string)            // removal event id
		if token != "" && eventID != "" {                  // save off-repo
			dir := filepath.Join(os.Getenv("HOME"), ".iprx") // private directory
			must(os.MkdirAll(dir, 0o700))                   // create it if needed
			path := filepath.Join(dir, eventID+".token")    // ~/.iprx/<event_id>.token
			must(os.WriteFile(path, []byte(token+"\n"), 0o600)) // owner read/write only
			fmt.Fprintf(os.Stderr, "# token saved privately to %s (mode 600); include it in your DKIM-signed .eml\n", path)
		}
	}
}

func solvePow(challenge string, bits int) string { // find a nonce with enough leading zero bits
	for n := 0; ; n++ {
		sum := sha256.Sum256([]byte(fmt.Sprintf("%s:%d", challenge, n)))
		if leadingZeroBits(sum[:]) >= bits {
			return strconv.Itoa(n)
		}
	}
}

func leadingZeroBits(digest []byte) int { // count leading zero bits in a hash
	zeros := 0
	for _, b := range digest {
		if b == 0 {
			zeros += 8
			continue
		}
		for mask := byte(0x80); mask != 0 && b&mask == 0; mask >>= 1 {
			zeros++
		}
		break
	}
	return zeros
}

func getJSON(url string, dest any) error { // GET JSON into dest
	resp, err := http.Get(url)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	return json.NewDecoder(resp.Body).Decode(dest)
}

func postJSON(url string, body any) (int, []byte) { // POST JSON and return status + raw body
	payload, err := json.Marshal(body)
	must(err)
	resp, err := http.Post(url, "application/json", bytes.NewReader(payload))
	must(err)
	defer resp.Body.Close()
	raw, err := io.ReadAll(resp.Body)
	must(err)
	return resp.StatusCode, raw
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
