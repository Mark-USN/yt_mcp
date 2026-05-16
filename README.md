Log File Locations:
C:\Users\mhenw\AppData\Local\HenCode\yt_mcp\Logs\yt_mcp.log
C:\Users\mhenw\AppData\Local\HenCode\universal_client\Logs\universal_client.log
C:\Users\mhenw\AppData\Local\HenCode\universal_client\Cache\VideoId(.txt and .json)
C:\ProgramData\mcp_server\logs\mcp_server.log
C:\ProgramData\mcp_server\data\transcripts\VideoId(.json and .lock)
C:\ProgramData\yt_mcp\logs\mcp_service(.err, .out, and .wrapper)
".wrapper": "WinSW log file"
".out": "mcp_server http log"
".err": "Errors during mcp_server execution"


WinSW Help:
A wrapper binary that can be used to host executables as Windows services

Usage: winsw <command> [<args>]
       Missing arguments triggers the service mode

Available commands:
  install     install the service to Windows Service Controller
  uninstall   uninstall the service
  start       start the service (must be installed before)
  stop        stop the service
  stopwait    stop the service and wait until it's actually stopped
  restart     restart the service
  restart!    self-restart (can be called from child processes)
  status      check the current status of the service
  test        check if the service can be started and then stopped
  testwait    starts the service and waits until a key is pressed then stops the service
  version     print the version info
  help        print the help info (aliases: -h,--help,-?,/?)

Extra options:
  /redirect   redirect the wrapper's STDOUT and STDERR to the specified file

WinSW 2.12.0.0
More info: https://github.com/winsw/winsw
Bug tracker: https://github.com/winsw/winsw/issues