Get-CimInstance Win32_Process |
  Where-Object {
    $_.CommandLine -match "lib\.mcp_servers\.(mcp_server|long_job_server)"
  } |
  Select-Object ProcessId, ParentProcessId, Name, CommandLine
