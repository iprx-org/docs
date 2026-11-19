#!/usr/bin/env node
// Download one event receipt as JSON, HTML, and PDF, plus the whole-IP bundle.
// Usage: node receipts.mjs [hash_id_or_event_id] [ipv4] [outdir]

import { mkdir, writeFile, stat } from "node:fs/promises"; // write the downloaded bytes
import { join } from "node:path";                          // build output paths

const BASE = process.env.IPRX_BASE || "https://iprx.org"; // set IPRX_BASE only if you use a different host
const KEY = process.argv[2] || "2c7606c0d53d7a800192f11609c939e66826f2af9c93fc971b850a97d5937466"; // 192.0.2.1 add event
const IP = process.argv[3] || "192.0.2.1";                // address for the bundle
const OUT = process.argv[4] || "/tmp/iprx-receipts";      // where to save the files
await mkdir(OUT, { recursive: true });                    // create the folder if needed

async function fetchTo(url, dest) {                       // GET a URL to a local file
  const resp = await fetch(url);                          // download
  if (!resp.ok) throw new Error(`HTTP ${resp.status} for ${url}`); // fail loudly
  const buf = Buffer.from(await resp.arrayBuffer());      // raw bytes (PDF is binary)
  await writeFile(dest, buf);                             // write the file
  const info = await stat(dest);                          // size
  console.log(`${dest}: ${info.size} bytes`);             // confirm it landed
}

await fetchTo(`${BASE}/api/v1/receipts/${KEY}.json`, join(OUT, "receipt.json")); // canonical JSON
await fetchTo(`${BASE}/api/v1/receipts/${KEY}.html`, join(OUT, "receipt.html")); // printable HTML
await fetchTo(`${BASE}/api/v1/receipts/${KEY}.pdf`, join(OUT, "receipt.pdf"));   // PDF
await fetchTo(`${BASE}/api/v1/receipts/ip/${IP}.json`, join(OUT, "bundle.json")); // whole-IP bundle
