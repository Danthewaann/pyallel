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
usage: pyallel [-h] [-t] [-n] [-V] [--colour {yes,no,auto}] [commands ...]

run and handle the output of multiple executables in pyallel (as in parallel)

RUNNING COMMANDS
================
to run multiple commands you must separate them using the command separator symbol (::)

  pyallel mypy . :: black .

if you want to provide options to a command you need to use the double dash symbol (--) to indicate that
any options provided after this symbol should not be interpreted by pyallel

  pyallel -n -- mypy -V :: black --version

commands can also be grouped using the group separator symbol (:::)

  pyallel echo boil kettle :: sleep 1 ::: echo make coffee

the above will print 'boil kettle' and sleep for 1 second first before printing 'make coffee'.
command groups are ran in the sequence you provide them, and if a command within a command group fails,
the rest of the command groups in the sequence are not run

modifiers can also be set for commands to augment their behaviour using the command modifier symbol (::::)

lines (only used in interactive mode):
  the lines modifier allows you to specify how many lines the command output can take up on the screen

    pyallel lines=90 :::: echo running long command... :: echo running other command...

  90 is expressed as a percentage value, which must be between 1 and 100 inclusive

SHELL SYNTAX
============
each command is executed inside its own shell, this means shell syntax is supported.
it is important to note that certain shell syntax must be escaped using backslashes (\)
or wrapped in single quotes (''), otherwise it will be evaluated in your current
shell immediately instead of the shell that your command will run within.

some examples of using shell syntax are below (single quotes are used only if required)

  pyallel MYPY_FORCE_COLOR=1 mypy .            <- provide environment variables
  pyallel 'mypy . | tee -a mypy.log'           <- use pipes to redirect output
  pyallel 'cat > test.log <<< hello!'          <- use input and output redirection
  pyallel 'mypy .; pytest .'                   <- run commands one at a time in sequence
  pyallel 'echo $SHELL; $(echo mypy .)'        <- expand variables and commands to evaluate
  pyallel 'pytest . && mypy . || echo failed!' <- use AND (&&) and OR (||) to run commands conditionally

positional arguments:
  commands              list of commands and their arguments to run in parallel

options:
  -h, --help            show this help message and exit
  -t, --no-timer        don't time how long each command is taking
  -n, --non-interactive
                        run in non-interactive mode
  -V, --version         print version and exit
  --colour {yes,no,auto}
                        colour terminal output, defaults to "auto"
```

Currently you can provide a variable number of `commands` to run to `pyallel`, like so:

```bash
pyallel MYPY_FORCE_COLOR=1 mypy . :: black --check --diff . :: pytest .
```

# Build

You can also build an executable with the following (executables will be written to `./dist`):

> [!NOTE]
> The `arch=x86_64` values in the following code blocks can be replaced with `arch=aarch64` and
> any other architecture that is supported by docker to build an executable for that given architecture

> [!NOTE]
> To build aarch64 binaries on an x86_64 host machine, you will need to run the following
> commands to setup qemu to allow this to work

```bash
sudo apt-get install qemu binfmt-support qemu-user-static && \
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

#### Build for generic linux

```bash
docker build --tag pyallel --build-arg 'arch=x86_64' --build-arg "uid=$(id -u)" . && \
    docker run -e 'arch=x86_64' --rm --volume "$(pwd):/src" pyallel
```

#### Build for alpine linux

```bash
docker build --tag pyallel-alpine --build-arg 'arch=x86_64' --build-arg "uid=$(id -u)" --file Dockerfile.alpine . && \
    docker run -e 'arch=x86_64' --rm --volume "$(pwd):/src" pyallel-alpine
```

#### Build locally

```bash
python -m venv .venv && \
  source .venv/bin/activate && \
  pip install . -r requirements_build.txt && \
  ./build.sh
```

#### Build all

```bash
./build_all.sh
```

## TODOs

- [x] Add support to have commands depend on other commands (some commands must complete
      before a given command can start)
- [x] Add support to state how many lines a command can use for it's output in interactive mode
- [x] Improve printing of output performance by only printing lines that have changed
- [ ] Add a debug mode that logs debug information to a log file
- [ ] Maybe add support to allow the user to provide stdin for commands that request it
      (such as a REPL)
- [ ] Add custom parsing of command output to support filtering for errors (like vim's
      `errorformat`)
- [ ] Allow list of files to be provided to supply as input arguments to each command
- [ ] Allow input to be piped into `pyallel` via stdin to supply as standard input to each
      command
