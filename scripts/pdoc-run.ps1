Set-Location $PSScriptRoot\..
$env:PYTHONPATH = ".\src"
pdoc readme yt_mcp yt_mcp_service debug_stub modules -o .\docs

.\Scripts\remove-usernames.ps1