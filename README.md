# yt_mcp

A FastMCP-based YouTube transcript and search server with support for:

* YouTube search
* Transcript retrieval
* Audio transcription
* MCP tools, prompts, and resources
* Windows service hosting via WinSW
* OpenAI-assisted query normalization

The project includes:

* `yt_mcp.py` — command-line server/client driver
* `yt_mcp_service.py` — Windows service manager
* MCP tools, prompts, and resources
* A universal MCP test client

---

# Features

* FastMCP server implementation
* YouTube transcript retrieval
* YouTube search integration
* OpenAI-assisted query normalization
* Audio transcription support
* Dynamic MCP resource registration
* Windows service support via WinSW
* Universal MCP test client

---

# Installation

```bash
git clone https://github.com/Mark-USN/yt_mcp.git
cd yt_mcp
uv sync
```

## Python Version

Python 3.12 or 3.13 is recommended.

Python 3.14 is currently unsupported because the `youtube_audio_transcript` tool depends on packages that do not yet fully support Python 3.14.

---

# Environment Variables

Create a `.env` file in the project root directory.

Example:

```env
GOOGLE_KEY="your_google_api_key"
OPENAI_KEY="your_openai_api_key"
```

## API Key Usage

| Key          | Purpose                                                    |
| ------------ | ---------------------------------------------------------- |
| `GOOGLE_KEY` | Used by the YouTube search tool                            |
| `OPENAI_KEY` | Used by the client for OpenAI-assisted query normalization |

The server will not start without `GOOGLE_KEY`.

The client will not run OpenAI-assisted query normalization without `OPENAI_KEY`.

---

# Quick Start

## Start the Server

```bash
uv run ./src/yt_mcp.py --mode server
```

```text
15:19:54 INFO yt_mcp [taskName=None] Starting MCP server with runtime=user, host=127.0.0.1, port=8085, debug=False
15:19:54 INFO yt_mcp [taskName=None] lib.mcp_servers.mcp_server started (detached) on http://127.0.0.1:8085.
15:19:54 INFO yt_mcp [taskName=None] Launching subprocess (output -> C:\Users\UserName\AppData\Local\HenCode\yt_mcp\Logs\mcp_server.log)
15:19:54 INFO yt_mcp [taskName=None] Server started (detached) on http://127.0.0.1:8085.
15:19:54 INFO yt_mcp [taskName=None] ℹ    PID: 24908.
15:19:54 INFO yt_mcp [taskName=None] ℹ    Log: C:\Users\UserName\AppData\Local\HenCode\yt_mcp\Logs\mcp_server.log.
```

## Run the Client

```bash
uv run ./src/yt_mcp.py --mode client
```
Partial output:

```text
15:22:44 INFO mcp.client.streamable_http [taskName=mcp.client.streamable_http.StreamableHTTPTransport.post_writer.<locals>.handle_request_async] Received session ID: 5b620dd4ea5d449ba90a3684b2f43856
15:22:44 INFO mcp.client.streamable_http [taskName=mcp.client.streamable_http.StreamableHTTPTransport.post_writer.<locals>.handle_request_async] Negotiated protocol version: 2025-11-25

=============== Ping the MCP Server.

15:22:44 INFO yt_mcp.mcp_clients.universal_client [taskName=Task-1] ping
True

=============== List available Tools.

15:22:44 INFO yt_mcp.mcp_clients.universal_client [taskName=Task-1]

Available Tools:
15:22:44 INFO yt_mcp.mcp_clients.universal_client [taskName=Task-1] Tool: add
15:22:44 INFO yt_mcp.mcp_clients.universal_client [taskName=Task-1] Tool: multiply
15:22:44 INFO yt_mcp.mcp_clients.universal_client [taskName=Task-1] Tool: youtube_search
15:22:44 INFO yt_mcp.mcp_clients.universal_client [taskName=Task-1] Tool: youtube_video_info
15:22:44 INFO yt_mcp.mcp_clients.universal_client [taskName=Task-1] Tool: youtube_playlist_info
15:22:44 INFO yt_mcp.mcp_clients.universal_client [taskName=Task-1] Tool: youtube_playlist_video_list
15:22:44 INFO yt_mcp.mcp_clients.universal_client [taskName=Task-1] Tool: youtube_json
15:22:44 INFO yt_mcp.mcp_clients.universal_client [taskName=Task-1] Tool: youtube_text
15:22:44 INFO yt_mcp.mcp_clients.universal_client [taskName=Task-1] Tool: youtube_sentences

=============== List available Resources.

15:22:44 INFO yt_mcp.mcp_clients.universal_client [taskName=Task-1]

Available Resources:
15:22:44 INFO yt_mcp.mcp_clients.universal_client [taskName=Task-1] Resource: resource://greeting
15:22:44 INFO yt_mcp.mcp_clients.universal_client [taskName=Task-1] Resource: data://config
15:22:44 INFO yt_mcp.mcp_clients.universal_client [taskName=Task-1] Resource: resource://UnicodeTable.md
15:22:44 INFO yt_mcp.mcp_clients.universal_client [taskName=Task-1] Resource: resource://Public/1.txt
15:22:44 INFO yt_mcp.mcp_clients.universal_client [taskName=Task-1] Resource: resource://Public/2.txt
15:22:44 INFO yt_mcp.mcp_clients.universal_client [taskName=Task-1] Resource: resource://Public/3.txt
15:22:44 INFO yt_mcp.mcp_clients.universal_client [taskName=Task-1] Resource: file://countries.json/
15:22:44 INFO yt_mcp.mcp_clients.universal_client [taskName=Task-1] Resource: resource://Public

=============== List available Templates.

15:22:44 INFO yt_mcp.mcp_clients.universal_client [taskName=Task-1]

Available Resource Templates:
15:22:44 INFO yt_mcp.mcp_clients.universal_client [taskName=Task-1] Template: weather://{city}/current
15:22:44 INFO yt_mcp.mcp_clients.universal_client [taskName=Task-1] Template: repos://{owner}/{repo}/info

=============== List available Prompts.

15:22:44 INFO yt_mcp.mcp_clients.universal_client [taskName=Task-1]

Available Prompts:
15:22:44 INFO yt_mcp.mcp_clients.universal_client [taskName=Task-1] Prompt: youtube_query_normalizer
15:22:44 INFO yt_mcp.mcp_clients.universal_client [taskName=Task-1] Prompt: summarize_text

```
>[!NOTE]
> The above output shows the available tools, resources, templates, and prompts that the client can interact with. The actual output goes on to run several test and display a lot of information that would just waste space here.

## Stop the Server

```bash
uv run ./src/yt_mcp.py --mode stop-server
```

---

# yt_mcp.py

`yt_mcp.py` is the primary command-line driver used to interact with the YouTube MCP server.

By default, the server launches on:

* Host: `127.0.0.1`
* Port: `8085`

The user may also specify custom `--host` and `--port` values.

## Modes

| Mode          | Description                                       |
| ------------- | ------------------------------------------------- |
| `server`      | Start the server in a background process          |
| `stop-server` | Stop the running server                           |
| `client`      | Run the `universal_client` to exercise the server |

## Debug Mode

The optional `--debug` flag causes the server to run in the foreground rather than launching as a detached background process.

When debug mode is enabled, `yt_mcp.py` will wait until the server exits before returning control to the command line.

## Client Capabilities

The client can:

* List all MCP tools
* List prompts
* List resources
* List resource templates
* Exercise YouTube search tools
* Exercise transcript tools
* Demonstrate OpenAI-assisted query normalization

The test sections of the client are specific to the YouTube MCP server implementation but also provide useful examples of how an AI agent might interact with an MCP server.

---

# yt_mcp_service.py

`yt_mcp_service.py` runs the YouTube MCP server as a Windows service.

This functionality uses `WinSW.exe`, renamed to `mcp_service.exe`, which reads the `mcp_server.xml` configuration file when launched.

## Service Modes

| Mode                | Description                                    |
| ------------------- | ---------------------------------------------- |
| `start-service`     | Install and start the service if necessary     |
| `stop-service`      | Stop the running service                       |
| `uninstall-service` | Stop and uninstall the service                 |
| `client`            | Run the `universal_client` against the service |

## Examples

### Install and Start the Service

```bash
uv run ./src/yt_mcp_service.py --mode start-service
```
>[!NOTE]
> If run on windows a UAC (User Account Control) prompt will appear asking for permission to run the command with elevated permissions. This is required to install and start the service.

### Run the Client

```bash
uv run ./src/yt_mcp_service.py --mode client
```

>[!NOTE]
> This will run the same `universal_client` as `yt_mcp.py --mode client` but it will interact with the MCP server running as a service rather than a user-mode server.

### Stop the Service

```bash
uv run ./src/yt_mcp_service.py --mode stop-service
```

>[!NOTE]
> If run on windows a UAC (User Account Control) prompt will appear asking for permission to run the command with elevated permissions. This is required to install and start the service.

---

# WinSW Commands

In practice, using `mcp_service.exe` directly is just as easy as using `yt_mcp_service.py`.

## Supported Commands

| Command     | Description                                                |
| ----------- | ---------------------------------------------------------- |
| `install`   | Install the service into the Windows Service Controller    |
| `uninstall` | Remove the service                                         |
| `start`     | Start the service                                          |
| `stop`      | Stop the service                                           |
| `stopwait`  | Stop the service and wait until it fully stops             |
| `restart`   | Restart the service                                        |
| `restart!`  | Self-restart from child processes                          |
| `status`    | Display service status                                     |
| `test`      | Verify the service can start and stop                      |
| `testwait`  | Start the service and wait for a key press before stopping |
| `version`   | Display version information                                |
| `help`      | Display command help                                       |

## Examples

### Display Service Status

```bash
mcp_service.exe status
```

### Install the Service

```bash
mcp_service.exe install
```

### Start the Service

```bash
mcp_service.exe start
```

### Stop the Service

```bash
mcp_service.exe stop
```

### Uninstall the Service

```bash
mcp_service.exe uninstall
```

> [!NOTE]
> Most service-management commands require elevated permissions.


---

# Logging and Cache Locations

## User Mode

```text
C:\Users\User_Name\AppData\Local\HenCode\yt_mcp
C:\Users\User_Name\AppData\Local\HenCode\MCP_Server
C:\Users\User_Name\AppData\Local\HenCode\universal_client
```

## Service Mode

```text
C:\ProgramData\mcp_server\logs\mcp_server.log
C:\ProgramData\yt_mcp\logs\mcp_service.err
C:\ProgramData\yt_mcp\logs\mcp_service.out
C:\ProgramData\yt_mcp\logs\mcp_service.wrapper
```

## Service Log Descriptions

| File       | Purpose                     |
| ---------- | --------------------------- |
| `.wrapper` | WinSW log file              |
| `.out`     | MCP server HTTP log         |
| `.err`     | MCP server execution errors |

---

# Requirements

## ffmpeg

`ffmpeg` is required and must be available in the system `PATH`.

It is used for processing video and audio data required by the `youtube_audio_transcript` tool.

Official site:

* [https://ffmpeg.org/](https://ffmpeg.org/)

## WinSW

`WinSW.exe` is required for running the YouTube MCP server as a Windows service.

It should be:

1. Placed in the project root directory
2. Renamed to `mcp_service.exe`

`mcp_service.exe` reads the `mcp_server.xml` configuration file to determine service parameters such as:

* Service name
* Host
* Port
* Logging configuration

Official site:

* [https://github.com/winsw/winsw](https://github.com/winsw/winsw)

---

# Warnings

> [!WARNING]
> Python installations obtained through the Microsoft Store may alter expected filesystem and PATH behavior, which can affect logging and environment discovery.
>
> A standard Python.org installation is recommended.
