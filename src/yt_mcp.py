""" 20251010 MMH yt_mcp.py
    A driver program to start/stop a detached MCP server or run a client. 

    USAGE: yt_mcp.py --mode server|client|stop-server, 
                [--host HOST] [--port PORT] [--debug True/False]
    Parameters:
        --mode: "server" to start a detached server, "client" to run a client,
                "stop-server" to stop a detached server.
        --host: Hostname or IP address (default 127.0.0.1)
        --port: TCP port number (default 8085)
        --debug: If True, launch server as child process; if False, launch
                 as detached process (default False)
"""

import sys
import os
import shutil
import argparse
import asyncio
import subprocess
import signal
from pathlib import Path
from yt_lib.utils import log_utils
from yt_lib.utils.app_context import RuntimeContext, create_user_context
from modules.mcp_servers import mcp_server
from modules.mcp_servers.mcp_server import ServerRuntime
from modules.mcp_clients.mcp_client_gui import McpClientApp

ctx = RuntimeContext(
    ctx=create_user_context(
        app_name="yt_mcp",
        app_author="ChickenScratch",
        app_dir=Path(__file__).parent.resolve(),
    )
)
# -----------------------------
# Logging setup
# -----------------------------
log_utils.configure_logging(
                log_utils.LogConfig(ctx.app_name, log_level="INFO"),
                file_log_conf=log_utils.FileLogConfig(log_file=ctx.log_path),
                force=True,
                tee_console=True,
            )
logger = log_utils.get_logger(__name__)

# ---- Helper to find pythonw.exe on Windows ----
# On Windows, we want to use pythonw.exe to avoid a console window popping up.
def _pythonw_exe():
    """ 20251101 MMH _pythonw_exe
        Return the path to pythonw.exe if on Windows, else sys.executable.
        This is the python interpreter used to launch the detached server process. 
        On Windows, we prefer pythonw.exe to avoid a console window.
    """
    # Prefer side-by-side pythonw next to the current interpreter
    exe = sys.executable
    if exe.lower().endswith("python.exe"):
        candidate = exe[:-10] + "pythonw.exe"
        if os.path.exists(candidate):
            return candidate
    # Fallback to PATH
    return shutil.which("pythonw.exe") or exe  # last resort: python.exe


# ---- Background launcher (detached subprocess) ----
def start_server(host: str, port: int, debug: bool):
    """ 20251101 MMH start_server
        Launches the MCP server as either a child process or as a detached process,
        depending on the debug flag. False will launch a detached process.
        20251214 MMH: Added mode parameter to select between demo_server and long_job_server.
    """
    server_pid_file = ctx.cache_dir / "mcp.pid" if isinstance(ctx.cache_dir, Path) else \
                        Path(f"{ctx.cache_dir}/mcp.pid")
    svr_log = ctx.log_dir / "mcp_server.log" if isinstance(ctx.log_dir, Path) else \
                Path(f"{ctx.log_dir}/mcp_server.log")

    runtime = ServerRuntime.USER
    logger.info("Starting MCP server with runtime=%s, host=%s, port=%i, debug=%s",
                runtime, host, port, debug)
    if debug:
        # Launch the server in the current process (foreground) for debugging.
        mcp_server.launch(runtime, host, port)
        return

    # --- Detached mode ---
    # When running in VS 2026 Debug mode, the subprocess will inherit
    # the parent's console window, which results in the server terminating
    # when the parent exits.

    # -------------------------------------------------------------
    # Paths for server PID & LOG files (used in detached mode)
    # -------------------------------------------------------------
    # Command line to run the server module as a separate process.  Launched through the 'if
    # __name__ == "__main__"' guard in mcp_server.py, which calls main() with the appropriate
    # arguments.

    cmd_str = "lib.mcp_servers.mcp_server"

    cmd = [
        _pythonw_exe(),
        "-m",
        cmd_str,
        "--runtime", runtime.value,
        "--host", host,
        "--port", str(port),
    ]

    # Platform-specific detachment options
    kwargs: dict = {}
    if os.name == "nt":
        flags = (
            subprocess.CREATE_NO_WINDOW
            | subprocess.CREATE_NEW_PROCESS_GROUP
        )
        kwargs["creationflags"] = flags
        # NOTE: no close_fds here on Windows, because of redirected std handles
    else:
        kwargs["start_new_session"] = True  # pylint: disable=no-member
        kwargs["close_fds"] = True

    # Use `with` for the log file only; the server keeps running after this
    # script exits.
    logger.info("%s started (detached) on http://%s:%i.", cmd_str, host, port)
    logger.info("Launching subprocess (output -> %s)", svr_log)
    with open(svr_log, "a",
              buffering=1,
              encoding="utf-8",
              errors="replace") as log_fh:
        # pylint: disable=consider-using-with
        proc = subprocess.Popen(
            cmd,
            stdout=log_fh,
            stderr=log_fh,
            stdin=subprocess.DEVNULL,
            cwd=str(Path(__file__).resolve().parent),
            **kwargs,
        )

    # At this point:
    #   - Child process is running independently
    #   - log_fh is closed in the parent (child still has its own handles)
    #   - We only keep and record the PID
    server_pid_file.write_text(str(proc.pid), encoding="utf-8")
    logger.info("Server started (detached) on http://%s:%i.", host, port)
    log_utils.log_tree(
        logger,
        log_utils.DEBUG,
        "subprocess",
        {
            "pid": proc.pid,
            "args": proc.args,
            "returncode": proc.returncode,
        },
        # collapse_keys={"env"},  # env can be huge/noisy
        # redact_keys={"token", "api_key"},
    )
    logger.info("ℹ    PID: %i.", proc.pid)
    logger.info("ℹ    Log: %s.", svr_log)


def stop_server():
    """ 20251101 MMH stop_server
        Stop a previously started detached server using the PID file.
    """
    server_pid_file = ctx.cache_dir / "mcp.pid" if isinstance(ctx.cache_dir, Path) else \
                        Path(f"{ctx.cache_dir}/mcp.pid")

    if not server_pid_file.exists():
        logger.error("No PID file found; server may not be running.")
        return

    try:
        pid = int(server_pid_file.read_text(encoding="utf-8").strip() or "0")
    except ValueError:
        logger.error("No PID file found; server may not be running.")
        return

    if pid <= 0:
        logger.error("No PID file found; server may not be running.")
        return

    # Try to terminate cross-platform
    try:
        if os.name == "nt":
            # Use taskkill to terminate the process tree reliably on Windows
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                           check=True, capture_output=True, text=True)
        else:
            os.kill(pid, signal.SIGTERM)
            logger.info("ℹ Sent stop signal to PID %i.", pid)
    except Exception as exc:                                        # pylint: disable=broad-except
        logger.error("Process %i not found, error = %s.", pid, exc)
        # raise SystemExit(f"Process {pid} not found.  Error = {exc}") from e

    # Clean up PID file regardless (best-effort)
    # Remove the old PID files if present
    server_pid_file.unlink(missing_ok=True)


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
        description="Create and run an MCP server or client."
    )

    parser.add_argument("--mode",
        choices=["server", "client", "stop-server"],
        type=str.lower,
        required=True,
        help="Run as server, client, or stop-server."
    )

    parser.add_argument("--host", type=str, default="127.0.0.1",
                        help="Host name or IP address (default 127.0.0.1).")
    parser.add_argument("--port", type=port_type, default=8085,
                        help="TCP port to bind/connect (default 8085).")
    parser.add_argument("--debug", action="store_true",
                        help="Lauch the server as a child of this Process "
                        "(True) or as a seperate Process (False).\n The "
                        "default is False")
    args = parser.parse_args()

    # 20251215 MMH Show help if no arguments are given
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)  # Exit with an error code

    if args.mode == "server":
        # Parent: launch a detached child and return immediately
        start_server(args.host, args.port, args.debug)
        # Parent exits now; detached child continues running.

    elif args.mode == "stop-server":
        stop_server()

    elif args.mode == "client":
        client = McpClientApp(host=args.host, port=args.port)
        asyncio.run(client.run())

if __name__ == "__main__":
    # If run as a script, execute main().
    main()
