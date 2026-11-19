# Check whether one IPv4 address is listed, and why.
# Usage: pwsh Check.ps1 [[-Ip] <ipv4>]
# The response includes nomination_progress, for example "3/5".

param(                                                    # script parameters
    [string]$Ip = "192.0.2.1"                             # first argument, or TEST-NET-1
)                                                         # end of the parameter block
$Base = if ($env:IPRX_BASE) { $env:IPRX_BASE } else { "https://iprx.org" }  # set IPRX_BASE only if you use a different host
$Url = "$Base/api/v1/check/$Ip"                           # path is /api/v1/check/{ip}
$Resp = Invoke-RestMethod -Uri $Url -Method Get           # GET the URL and parse JSON
$Resp | ConvertTo-Json -Depth 8                           # print a readable document
