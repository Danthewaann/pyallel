# Pyallel

Run and handle the output of multiple executables in `pyallel` (as in parallel)

# Quick start

`pyallel` can be installed using pip:

```bash
pip install pyallel
```

Once installed, you can run `pyallel` to see usage information, like so:

```bash
pyallel
```

Currently you can provide a variable number of `commands` to run to `pyallel`, like so:

> [!IMPORTANT]
> If your need to provide arguments to a command, you must surround the command and it's arguments in quotes!

```bash
pyallel "black --color --check --diff ." "mypy ." "ruff check --no-fix ."
```

## TODOs

- [ ] Allow list of files to be provided to supply as input arguments to each command
- [ ] Allow input to be piped into `pyallel` via stdin to supply as standard input to each
      command
- [ ] Add custom config file for `pyallel` to read from as an alternative to providing
      arguments via the command line
- [ ] Add support for providing config via a `pyproject.toml` file in the current
      working directory
- [ ] Add test suite
- [ ] Improve error handling when parsing provided commands (check they are valid executables)
- [ ] Add visual examples of `pyallel` in action
