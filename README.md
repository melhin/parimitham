# Parimitham - Django with Python Subinterpreters

A demonstration project showing how to run Django applications using Python's subinterpreters.

## Features

- Single-file Django project architecture
- Background task processing with Django Tasks (SQLite backend)
- Multi-worker setup using Python subinterpreters
- Based on [subinterpreter-web](https://github.com/tonybaloney/subinterpreter-web) architecture

## Prerequisites

- Python 3.14+ (required for subinterpreters)
- [uv package manager](https://docs.astral.sh/uv/)

## Quick Start

1. Clone the repository
2. Install dependencies:
```sh
uv sync
```

3. Start web and task workers in different interpreters:
```bash
uv run up.py -w 4 -t 2 -b 127.0.0.1:8001
```


## Available Endpoints

- **Task Enqueue Endpoint**: [http://127.0.0.1:8001/](http://127.0.0.1:9001/)
  - Synchronous endpoint that enqueues a sample task
  - Returns immediately after task creation

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

 Help option:
```bash
uv run up.py -h
```

```
Django application with InterpreterPoolEExecutor
options:
  -h, --help            show this help message and exit
  -w, --workers WORKERS
                        The number of web workers to spawn and use
  -v, --verbose         Increase logging verbosity
  -a, --async-run       Run the async application
  -b, --bind BIND       Bind address for the web server
  -t, --task-workers TASK_WORKERS
                        Number of task workers
```
Example:
```bash
uv run up.py -w 4 -t 2 -b 127.0.0.1:8001
```
