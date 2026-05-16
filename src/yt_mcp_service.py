""" 20260414 MMH yt_mcp_service.py
    A driver program to install, start, stop and remove the MCP server as a service. 

    USAGE: yt_mcp_service.py --mode start-service|client|stop-service|uninstall-service, 
                [--host HOST] [--port PORT]
    Parameters:
        --mode: "start-service" to install the service if necessary and start the MCP server as
                a service,
                "client" to run a client, connect to the server and exercise it.
                "stop-service" to stop the MCP server service,
                "uninstall-service" to remove the MCP server service.
        --host: Hostname or IP address used in Client mode only.
        --port: TCP port number used in Client mode only.
    Note: The service management commands (start-service, stop-service, uninstall-service) are
    only supported on Windows at this time. The client mode can be run on any platform but 
    requires a server to be running and accessible at the specified host and port.   
    The MCP server's host and port are configured in the mcp_service.xml file, which is used by
    the service wrapper.
    If no host/port is specified on the command line for the client mode, it will attempt to read
    them from the mcp_service.xml
"""

import sys
import argparse
import asyncio
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from yt_lib.utils.log_utils import (
   LogConfig,
   FileLogConfig,
   configure_logging,
   get_logger,
)
from yt_lib.utils.app_context import RuntimeContext, create_user_context
from lib.mcp_clients.universal_client import UniversalClient

ctx = RuntimeContext(
    create_user_context(
        app_name="yt_mcp",
        app_author="HenCode",
        app_dir=Path(__file__).parent.resolve(),
    )
)

# -----------------------------
# Logging setup
# -----------------------------
configure_logging(
                LogConfig(ctx.app_name, log_level="INFO"),
                file_log_conf=FileLogConfig(log_file=ctx.log_path()),
                force=True,
                tee_console=True,
            )
logger = get_logger(__name__)

# Where to find the service wrapper executable and XML config,
# the wrapper is responsible for installing
PROJECT_ROOT = Path(ctx.app_dir.parent).resolve()
SERVICE_EXE = PROJECT_ROOT / "mcp_service.exe"


def run_service_command(command: str) -> str:
    """ Run a command on the service wrapper executable WinSW.exe (renamed mcp_server.exe)
        and return the combined stdout and stderr output. 
        Args:
            command: The command to run, e.g. "install", "start", "stop", "uninstall", "status".
        Returns:
            The combined stdout and stderr output from the command.
        Raises:
            FileNotFoundError: If the service wrapper executable is not found.

        Available WinSW commands:
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

        Note: The service wrapper executable must be run with appropriate permissions for certain
        commands, e.g. "install" and "uninstall" "Start" and "Stop" typically require administrator
        privileges.
    """
    if not SERVICE_EXE.exists():
        raise FileNotFoundError(f"Missing service wrapper: {SERVICE_EXE}")

    result = subprocess.run(
        [str(SERVICE_EXE), command],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    output = (result.stdout + result.stderr).strip()

    if result.returncode != 0:
        raise RuntimeError(
            f"Service command failed: {command}\n"
            f"Exit code: {result.returncode}\n"
            f"{output}"
        )

    return output


def service_status() -> str:
    """ Check the current status of the service by running the "status" command on the
        service wrapper. Does not require admin privileges. 
        Returns:
            The status string output from the command, which typically includes "Started",
            "Stopped", or "NonExistent" if the service is not installed.
    """
    return run_service_command("status")

def ensure_server_service_running() -> None:
    """ Ensure that the MCP server service is installed and running. If the service is not
        installed, install it. If it is installed but not running, start it. If it is already
        running, do nothing.
    """
    status = service_status()

    if "NonExistent" in status:
        run_service_command("install")
        # If started in 'manual' mode, the service will not start automatically after
        # installation, so start it explicitly.
        # run_service_command("start")
        return

    if "Stopped" in status:
        run_service_command("start")
        return

    if "Started" in status:
        logger.info("MCP server service is already running.")
        return

    raise RuntimeError(f"Unexpected service status: {status}")


def read_service_xml_host_port(xml_path: Path) -> tuple[str | None, int | None]:
    """ Read the host and port configuration from the service XML file.
        Args:
            xml_path: The path to the service XML configuration file.
        Returns:
            A tuple of (host, port) where host is a string or None, and port is an integer or None.
    """
    if not xml_path.exists():
        logger.error("Service XML configuration file not found: %s", xml_path)
        return None, None

    root = ET.parse(xml_path).getroot()

    values = {
        env.attrib.get("name"): env.attrib.get("value")
        for env in root.findall("env")
    }

    host = values.get("YTMCP_HOST")
    port_text = values.get("YTMCP_PORT")

    if host is None or port_text is None:
        return host, None

    try:
        port = int(port_text)
    except ValueError:
        return host, None

    return host, port

def resolve_client_connection(
        arg_host: str | None,
        arg_port: int | None,
        xml_path: Path,
    ) -> tuple[str, int]:
    """ Resolve the host and port for the client connection by checking command line arguments
        first, then falling back to the service XML configuration file.
        Args:
            arg_host: The host specified via command line argument.
            arg_port: The port specified via command line argument.
            xml_path: The path to the service XML configuration file.
        Returns:
            A tuple of (host, port) where host is a string and port is an integer.
        Raises:
            ValueError: If neither the command line arguments nor the XML configuration provide
                        valid host and port values.
    """
    xml_host, xml_port = read_service_xml_host_port(xml_path)

    host = arg_host or xml_host
    port = arg_port or xml_port

    if host is None or port is None:
        raise ValueError(
            "No host or port found or specified. Either start/configure the "
            "service or specify --host and --port."
        )

    return host, port

def port_type(value: str) -> int:
    """ 20251101 MMH port_type
        Custom argparse type that validates a TCP port number.
    """
    try:
        port = int(value)
    except ValueError as err:
        logger.error("Port must be an integer.\n%s Port = %s.",
            str(value), err)
        raise SystemExit(f"Port must be an integer.\n{value} Port = {err}") from err
    if not 1 <= port <= 65535:
        logger.error("Port number must be between 1 and 65535 (got {port!r})")
        raise SystemExit(
            f"Port number must be between 1 and 65535!. Port = {port}.") from err
    return port

def main():
    """ Main entry point: parse arguments and start/stop server or run client. """    
    parser = argparse.ArgumentParser(
        description="Create and run an MCP server or client. The host and port are only relevant "
                    "for the client mode."
    )

    parser.add_argument("--mode",
        choices=["start-service", "client", "stop-service", "uninstall-service"],
        type=str.lower,
        required=True,
        help="Run start-service, client, stop-service, or uninstall-service."
    )

    parser.add_argument("--host", type=str,
                        help="Host name or IP address (default 127.0.0.1).")
    parser.add_argument("--port", type=port_type,
                        help="TCP port to bind/connect (default 8085).")
    args = parser.parse_args()

    # 20251215 MMH Show help if no arguments are given
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)  # Exit with an error code

    match args.mode:
        case "start-service":
            ensure_server_service_running()

        case "stop-service":
            output = run_service_command("stop")
            logger.info("Service stop result: %s", output)

        case "uninstall-service":
            # If it is running it will not uninstall until it is stopped,
            # so stop it first just in case.
            output = run_service_command("stop")
            output = run_service_command("uninstall")
            logger.info("Service uninstall result: %s", output)

        case "client":
            # For the client, resolve host and port from command line arguments or service
            # XML config.
            host, port = resolve_client_connection(args.host, args.port,
                                                   Path(ctx.app_dir.parent / "mcp_service.xml"))
            client = UniversalClient(host, port)
            asyncio.run(client.run())

        case _:
            # This should not happen due to argparse choices, but include it for completeness.
            raise ValueError(f"Unknown mode: {args.mode}")

if __name__ == "__main__":
    # If run as a script, execute main().
    main()
