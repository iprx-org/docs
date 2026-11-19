# Search public, redacted records by hostname, IP, hash_id, ASN, ISP, or country.
# Usage: pwsh Search.ps1 [[-Query] <string>]

param(                                                    # script parameters
    [string]$Query = "nt-isp"                             # hostname substring or other public search term
)                                                         # end of the parameter block
$Base = if ($env:IPRX_BASE) { $env:IPRX_BASE } else { "https://iprx.org" }  # set IPRX_BASE only if you use a different host
$Url = "$Base/api/v1/search?q=$([uri]::EscapeDataString($Query))"  # GET /api/v1/search?q=
$Resp = Invoke-RestMethod -Uri $Url -Method Get           # GET the URL and parse JSON
$Resp | ConvertTo-Json -Depth 8                           # print a readable document
