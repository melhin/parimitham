# Parimitham - Django with Python Subinterpreters

A demonstration project showing how to run Django applications using Python's subinterpreters for task processing.

## What are Python Subinterpreters?

Python subinterpreters allow running multiple isolated Python interpreters within a single process..

## Features

- Single-file Django project architecture
- Background task processing with Django Tasks (SQLite backend)
- Multi-worker setup using Python subinterpreters
- Tasks are shared between subinterpreters using the newly available subinterpreter queues

## Prerequisites

- Python 3.14+ (required for subinterpreters)
- Django 5.0+
- [uv package manager](https://docs.astral.sh/uv/)

## Some interesting components

```
parimitham/
├── up.py              # Main subinterpreter application launcher
├── worker_task.py     # Makes a webserver based on hypercorn and a management command runnable in a subinterpreter
|                      # using the queues provided by the application launcher
└── queue_bridge.py    # Task queue bridging between subinterpreters
```

## Quick Start

1. Clone the repository
2. Install dependencies:
```sh
uv sync
```

3. Run database migrations:
```sh
uv run python manage.py migrate
```

4. Start web and task workers in different interpreters:
```bash
uv run up.py -w 4 -t 2 -b 127.0.0.1:8001
```

5. Access the application in your web browser at [http://127.0.0.1:8001/](http://127.0.0.1:8001/) or curl it:
```bash
curl http://127.0.0.1:8001/
```

6. Observe the logs to see task processing in action.

## Available Endpoints

- **Task Enqueue Endpoint**: [http://127.0.0.1:8001/](http://127.0.0.1:8001/)
  - Synchronous endpoint that enqueues a sample task
  - Returns immediately after task creation
  - View task processing in the logs

## Creating Custom Tasks

Example task definition:
```python
# tasks/sample_tasks.py
def process_data(data):
    # Your task logic here
    return f"Processed: {data}"
```

## Troubleshooting

### Common Issues

- **Port already in use**: Change the bind address with `-b` option
- **SQLite locked**: Ensure WAL mode is enabled (see SQLite section)
- **Import errors**: Run `uv sync` to install dependencies

## Performance Tuning

### SQLite Optimization

For better SQLite performance with concurrent access:

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

Available options:
- `-w, --workers`: Number of web workers (default: 2)
- `-t, --task-workers`: Number of task workers (default: 1)
- `-b, --bind`: Bind address (default: 127.0.0.1:8000)
- `-v, --verbose`: Enable verbose logging

Example:
```bash
uv run up.py -w 4 -t 2 -b 127.0.0.1:8001 -v
```