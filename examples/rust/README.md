# Rust examples

These are optional extras. They use the [`ureq`](https://crates.io/crates/ureq) crate for HTTPS because the Rust standard library has no HTTP client.

```bash
# from this directory
cargo run -- 192.0.2.1
```

`check.rs` is the complete program, with a comment on every line. Change the dependency version in `Cargo.toml` if you already use ureq 3.
