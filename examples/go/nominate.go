package main // this is a standalone program; run with: go run nominate.go
// Nominate one IPv4 address via POST /api/v1/nominations.
// Usage:
//   go run nominate.go [ipv4] [reason]                    // anonymous: solves the proof-of-work
//   IPRX_TOKEN=iprx_… go run nominate.go [ipv4] [reason]  // verified token: skips PoW, no rate limit
// Documentation, private, and reserved addresses are rejected with HTTP 400.

import (
	"bytes"         // wrap the JSON body as an io.Reader
	"crypto/sha256" // SHA-256 for the proof-of-work
	"encoding/json" // request and response JSON
	"fmt"           // print status and errors
	"io"            // read the response body
	"net/http"      // HTTP client
	"os"            // arguments and environment
	"strconv"       // convert the nonce counter to a string
)

func main() { // program entry point
	base := getenv("IPRX_BASE", "https://iprx.org")       // set IPRX_BASE only if you use a different host
	ip := arg(1, "192.0.2.10")                             // default TEST-NET is rejected on purpose
	reason := arg(2, "TEST documentation nomination from the IPRX examples; RFC 5737 TEST-NET.") // >= 8 chars
	name := getenv("IPRX_NAME", "IPRX examples TEST")      // your display name
	email := getenv("IPRX_EMAIL", "docs-test@example.com") // used to count distinct nominators
	token := os.Getenv("IPRX_TOKEN")                       // optional verified token; if set, skip the proof-of-work
	body := map[string]any{                                // NominationIn
		"ip":          ip,
		"reason":      reason,
		"evidence":    "TEST",
		"name":        name,
		"email":       email,
		"org":         "IPRX docs examples",
		"company_url": "", // honeypot; must stay empty
	}
	if token == "" { // anonymous path still needs a challenge
		ch := map[string]any{}                       // {challenge, bits, expires_in}
		must(getJSON(base+"/api/v1/challenge", &ch)) // fetch a one-time challenge
		challenge, _ := ch["challenge"].(string)     // opaque string
		bits := 18                                   // default difficulty
		if v, ok := ch["bits"].(float64); ok {       // JSON numbers decode as float64
			bits = int(v)                            // use the server's value
		}
		body["challenge"] = challenge                // opaque string from GET /challenge
		body["pow_nonce"] = solvePow(challenge, bits) // usually 18 leading zero bits
	}
	status, raw := postJSON(base+"/api/v1/nominations", body, token) // 201 on success, 400 for TEST-NET
	fmt.Println(status)                                    // HTTP status
	fmt.Println(string(raw))                               // body
}

func solvePow(challenge string, bits int) string { // find a nonce with enough leading zero bits
	for n := 0; ; n++ { // start at zero; any unique string works
		sum := sha256.Sum256([]byte(fmt.Sprintf("%s:%d", challenge, n))) // the API hashes this exact string
		if leadingZeroBits(sum[:]) >= bits { // hard enough
			return strconv.Itoa(n) // return the nonce as a decimal string
		}
	}
}

func leadingZeroBits(digest []byte) int { // count leading zero bits in a hash
	zeros := 0                 // running total
	for _, b := range digest { // left to right
		if b == 0 {            // a zero byte is eight bits
			zeros += 8
			continue
		}
		for mask := byte(0x80); mask != 0 && b&mask == 0; mask >>= 1 { // walk bits from the MSB
			zeros++
		}
		break // stop at the first non-zero byte
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

func postJSON(url string, body any, token string) (int, []byte) { // POST JSON and return status + raw body
	payload, err := json.Marshal(body)
	must(err)
	req, err := http.NewRequest(http.MethodPost, url, bytes.NewReader(payload)) // so we can set Authorization
	must(err)
	req.Header.Set("Content-Type", "application/json") // the nominations API expects JSON
	req.Header.Set("Accept", "application/json")       // ask for JSON
	if token != "" { // a verified token skips the proof-of-work
		req.Header.Set("Authorization", "Bearer "+token) // format: Authorization: Bearer iprx_…
	}
	resp, err := http.DefaultClient.Do(req)
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
