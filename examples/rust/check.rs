// Check whether one IPv4 address is listed, and why.
// Usage (from this directory): cargo run -- [ipv4]
// The response includes nomination_progress, for example "3/5".

fn main() { // program entry point
    let base = std::env::var("IPRX_BASE").unwrap_or_else(|_| "https://iprx.org".into()); // set IPRX_BASE only if you use a different host
    let ip = std::env::args().nth(1).unwrap_or_else(|| "192.0.2.1".into()); // first argument, or TEST-NET-1
    let url = format!("{}/api/v1/check/{}", base, ip); // path is /api/v1/check/{ip}
    let body = ureq::get(&url) // GET the URL
        .call() // send the request
        .expect("HTTP request failed") // stop on a transport or HTTP error
        .into_string() // read the body as text
        .expect("failed to read body"); // stop on a read error
    println!("{}", body); // print the JSON as received, including nomination_progress
}
