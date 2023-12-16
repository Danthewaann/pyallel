# Pyallel

Run and handle the output of multiple executables in `pyallel` (as in parallel)

Requires Python >=3.8

Tested on Linux and MacOS only

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
pyallel "black --color --check --diff ." "MYPY_FORCE_COLOR=1 mypy ." "ruff check --no-fix ."
```

## TODOs

- [ ] Allow output for all provided commands to be streamed to stdout (this will require a
      re-work of how we print command output as we currently just print output once the command
      finishes)
- [ ] Allow specific command outputs to be streamed to stdout, while all other
      commands will only get outputted after the streamed commands have completed (such as running
      `pytest` as a streamed command, whilst running `mypy`, `ruff` etc. as non-streamed commands).
      This will require adding special arguments/modes to each command so they are treated
      differently from other commands
- [x] Provide a way to set environment variables for each command to run with
- [ ] Allow list of files to be provided to supply as input arguments to each command
- [ ] Allow input to be piped into `pyallel` via stdin to supply as standard input to each
      command
- [ ] Add custom config file for `pyallel` to read from as an alternative to providing
      arguments via the command line
- [ ] Add support for providing config via a `[tool.pyallel]` section in a
      `pyproject.toml` file in the current working directory
- [ ] Maybe allow command dependencies to be defined in a python file where commands are
      decorated with info that details it's dependencies?
- [x] Add test suite
- [x] Improve error handling when parsing provided commands (check they are valid executables)
- [ ] Add visual examples of `pyallel` in action
