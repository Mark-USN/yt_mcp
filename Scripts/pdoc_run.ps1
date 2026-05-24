Set-Location $PSScriptRoot\..
$env:PYTHONPATH = ".\src"
pdoc YT_MCP_Readme yt_mcp yt_mcp_service debug_stub lib -o .\docs

.\Scripts\remove-usernames.ps1