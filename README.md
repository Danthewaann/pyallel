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
usage: pyallel [-h] [-t] [-n] [-s] [-V] [-v] [commands ...]

Run and handle the output of multiple executables in pyallel (as in parallel)

positional arguments:
  commands              list of quoted commands to run e.g "mypy ." "black ."

                        can provide environment variables to each command like so:

                             "MYPY_FORCE_COLOR=1 mypy ."

options:
  -h, --help            show this help message and exit
  -t, --timer           time how long each command is taking
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
        "pytest ."
```

## TODOs

- [x] Allow output for all provided commands to be streamed to stdout (this will require a
      re-work of how we print command output as we currently just print output once the command
      finishes)
- [x] Add CI checks to run the tests and linters against Python versions > 3.8
- [x] Add command mode arguments to support things like only tailing the last 10 lines
      of a command whilst it is running e.g. `"tail=10 :: pytest ."`
- [x] Add visual examples of `pyallel` in action
- [x] Fix bug in non-interactive streamed mode where all commands share the same amount of
      time taken as the longest running command
- [x] Fix bug in non-interactive streamed mode where calling `readline` doesn't
      account for `EOF` (if we are at `EOF` we shouldn't append a newline as more output could
      be appended to the current line)
- [x] Fix bug in streamed mode where we should use the number of terminal columns when
      determining when to truncate the line to fit within the screen (or properly handle wrapped
      lines)
- [x] Provide a way to set environment variables for each command to run with
- [x] Add test suite
- [x] Improve error handling when parsing provided commands (check they are valid executables)
- [x] Maybe make tail mode followed by an optional dump of all the command output once it
      finishes the default behaviour?
- [ ] Add graceful Ctrl-C interrupt handling
- [ ] Add custom parsing of command output to support filtering for errors (like vim's
      `errorformat`)
- [ ] Allow list of files to be provided to supply as input arguments to each command
- [ ] Allow input to be piped into `pyallel` via stdin to supply as standard input to each
      command
