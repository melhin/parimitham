# Parimitham - Django with Python Subinterpreters

A demonstration project showing how to run Django applications using Python's subinterpreters for task processing.

## What are Python Subinterpreters?

Python subinterpreters allow running multiple isolated Python interpreters within a single process.

## Features

- Single-file Django project architecture
- Background task processing with Django Tasks (both InterpreterQueue and DB-backed)
- Multi-worker setup using Python subinterpreters
- Tasks are shared between subinterpreters using the newly available subinterpreter queues

## Prerequisites

- Python 3.14+ (required for subinterpreters)
- Django 5.0+
- [uv package manager](https://docs.astral.sh/uv/)

## Project Structure

```
parimitham/
├── up.py              # Main subinterpreter application launcher
├── worker_task.py     # Web server based on Hypercorn and a management command runnable in a subinterpreter
|                      # using the queues provided by the application launcher
└── queue_bridge.py    # Task queue bridging between subinterpreters
```

## Quick Start

1. Clone the repository
2. Install the relevant Python version. If using pyenv:
```sh
pyenv install 3.14
```
3. Install dependencies:
```sh
uv sync
```

4. Start web and task workers in different interpreters:
   - Before starting, run an instance of PostgreSQL if you don't have one running. Use the provided Docker Compose option:
   ```bash
   docker compose up
   ```
   
   - Then run:
   ```bash
   uv run up.py -w 4 -t 2 -b 127.0.0.1:8001
   ```

5. Access the application in your web browser at [http://127.0.0.1:8001/](http://127.0.0.1:8001/) or use curl:
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

## Database Configuration

This project uses PostgreSQL as the default database backend. To set up the database:

1. Start PostgreSQL using Docker Compose:
```bash
docker compose up
```

2. The default configuration will connect to:
   - Host: localhost
   - Port: 5432
   - Database: parimitham
   - User: postgres
   - Password: postgres

## Troubleshooting

### Common Issues

- **Port already in use**: Change the bind address with the `-b` option
- **Database connection failed**: Ensure PostgreSQL is running via `docker compose up`
- **Import errors**: Run `uv sync` to install dependencies
- **Subinterpreter errors**: Verify you're using Python 3.14+


## Command Line Options

View help information:
```bash
uv run up.py -h
```

Available options:
- `-w, --workers`: Number of web workers (default: 2)
- `-t, --task-workers`: Number of task workers (default: 1)
- `-b, --bind`: Bind address (default: 127.0.0.1:8000)
- `-v, --verbose`: Enable verbose logging

Example usage:
```bash
uv run up.py -w 4 -t 2 -b 127.0.0.1:8001 -v
```