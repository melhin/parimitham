## What is this about ?

* A single file Django project
* A sample task run using django tasks
* Both HTTP and worker run using subinterpreter ( Adaptation of https://github.com/tonybaloney/subinterpreter-web )


## How to run ?

If you have [uv](https://docs.astral.sh/uv/) installed then it is a matter of couple of commands after cloning the repo.

```
uv sync
uv run run_dj.py -w 2 -v
```

You should see https workers and task workers being spawned.
