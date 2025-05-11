# Parimitham - Django with Python Subinterpreters

A demonstration project showing how to run Django applications using Python's subinterpreters.

## Features

- Single-file Django project architecture
- Background task processing with Django
- Multi-worker setup using Python subinterpreters
- Async endpoint for task result streaming
- Based on [subinterpreter-web](https://github.com/tonybaloney/subinterpreter-web) architecture

## Prerequisites

- Python 3.13+ (required for subinterpreters)
- [uv package manager](https://docs.astral.sh/uv/)

## Quick Start

1. Clone the repository
2. Install dependencies:
```sh
uv sync
```

3. Run the application with 2 workers:
```sh
uv run run_dj.py -w 2 -v
```

## Available Endpoints

- **Task Enqueue Endpoint**: [http://127.0.0.1:9001/](http://127.0.0.1:9001/)
  - Synchronous endpoint that enqueues a sample task
  - Returns immediately after task creation

- **Task Stream Endpoint**: [http://127.0.0.1:9002/stream/](http://127.0.0.1:9002/stream/)
  - Asynchronous endpoint that streams task execution results
  - Uses Server-Sent Events (SSE) for real-time updates

## Architecture

The application runs two types of workers:
- HTTP workers: Handle incoming web requests
- Task workers: Process background tasks

Both worker types run in separate Python subinterpreters.

## SQLite Optimization

For better SQLite performance, the following PRAGMA settings are recommended:

```sql
pragma journal_mode = WAL;        -- Use Write-Ahead Logging
pragma synchronous = normal;      -- Balance durability with performance
pragma temp_store = memory;       -- Store temporary tables in memory
pragma mmap_size = 30000000000;  -- Increase memory-mapped I/O size
```

## Command Line Options

Run the application with `-h` to see available options:
```sh
uv run run_dj.py -h
```

Key options:
- `-w, --workers`: Number of task workers (default: CPU count)
- `-v, --verbose`: Enable verbose logging
