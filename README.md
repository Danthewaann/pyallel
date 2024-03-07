# Pyallel

Run and handle the output of multiple executables in `pyallel` (as in parallel)

https://github.com/Danthewaann/pyallel/assets/22531177/8685eb92-aac5-440a-9170-30fd1460c53f

Tested on Linux and MacOS only

# Installation

Pre-built executables are available on the [Releases](https://github.com/Danthewaann/pyallel/releases) page.

`pyallel` can also be installed using pip (requires Python >=3.8):

```bash
pip install pyallel
```

# Quick start

Once installed, you can run `pyallel` to see usage information, like so:

```
usage: pyallel [-h] [-t] [-n] [-V] [-v] [--colour {yes,no,auto}] [commands ...]

Run and handle the output of multiple executables in pyallel (as in parallel)

positional arguments:
  commands              list of quoted commands to run e.g "mypy ." "black ."

                        can provide environment variables to each command like so:

                             "MYPY_FORCE_COLOR=1 mypy ."

options:
  -h, --help            show this help message and exit
  -t, --no-timer        don't time how long each command is taking
  -n, --non-interactive
                        run in non-interactive mode
  -V, --verbose         run in verbose mode
  -v, --version         print version and exit
  --colour {yes,no,auto}
                        colour terminal output, defaults to "auto"
```

Currently you can provide a variable number of `commands` to run to `pyallel`, like so:

> [!IMPORTANT]
> If you need to provide arguments to a command, you must surround the command and it's arguments in quotes!

```bash
pyallel "MYPY_FORCE_COLOR=1 mypy ." \
        "black --check --diff ." \
        "pytest ."
```

# Build

You can also build an executable with the following (executables will be written to `./dist`):

> [!NOTE]
> The `arch=x86_64` values in the following code blocks can be replaced with `arch=aarch64` and
> any other architecture that is supported by docker to build an executable for that given architecture

#### Build for generic linux

```bash
docker build --tag pyallel --build-arg 'arch=x86_64' . && docker run -e 'arch=x86_64' --rm --volume "$(pwd):/src" pyallel
```

#### Build for alpine linux

```bash
docker build --tag pyallel-alpine --build-arg 'arch=x86_64' --file Dockerfile.alpine . && docker run -e 'arch=x86_64' --rm --volume "$(pwd):/src" pyallel-alpine
```

#### Build locally

```bash
python -m venv .venv && source .venv/bin/activate && pip install . -r requirements_build.txt && ./build.sh
```

## TODOs

- [ ] Maybe add support for allowing commands to contain shell idiom's (such as piping
      e.g. `echo hi | tee test.log`)
- [ ] Add custom parsing of command output to support filtering for errors (like vim's
      `errorformat`)
- [ ] Allow list of files to be provided to supply as input arguments to each command
- [ ] Allow input to be piped into `pyallel` via stdin to supply as standard input to each
      command
