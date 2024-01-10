# Pyallel

Run and handle the output of multiple executables in `pyallel` (as in parallel)

https://github.com/Danthewaann/pyallel/assets/22531177/be12efc4-439d-416d-8112-dc57cc4c291a

Requires Python >=3.8

Tested on Linux and MacOS only

# Quick start

`pyallel` can be installed using pip:

```bash
pip install pyallel
```

Once installed, you can run `pyallel` to see usage information, like so:

```
usage: pyallel [-h] [-d] [-n] [-s] [-V] [-v] [commands ...]

Run and handle the output of multiple executables in pyallel (as in parallel)

positional arguments:
  commands              list of quoted commands to run e.g "mypy ." "black ."

                        can provide environment variables to each command like so:

                             "MYPY_FORCE_COLOR=1 mypy ."

                        command modes:

                        can also provide modes to commands to do extra things:

                            "tail=10 :: pytest ." <-- only output the last 10 lines, doesn't work in --no-stream mode

options:
  -h, --help            show this help message and exit
  -d, --debug           output debug info for each command
  -n, --non-interactive
                        run in non-interactive mode
  -s, --no-stream       don't stream output of each command
  -V, --verbose         run in verbose mode
  -v, --version         print version and exit
```

Currently you can provide a variable number of `commands` to run to `pyallel`, like so:

> [!IMPORTANT]
> If you need to provide arguments to a command, you must surround the command and it's arguments in quotes!

```bash
pyallel "MYPY_FORCE_COLOR=1 mypy ." \
        "black --check --diff ." \
        "tail=20 :: pytest ."
```

## TODOs

- [x] Allow output for all provided commands to be streamed to stdout (this will require a
      re-work of how we print command output as we currently just print output once the command
      finishes)
- [x] Add CI checks to run the tests and linters against Python versions > 3.8
- [x] Add command mode arguments to support things like only tailing the last 10 lines
      of a command whilst it is running e.g. `"tail=10 :: pytest ."`
- [x] Add visual examples of `pyallel` in action
- [ ] Add custom parsing of command output to support filtering for errors (like vim's
      `errorformat`)
- [ ] Add graceful Ctrl-C interrupt handling
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
