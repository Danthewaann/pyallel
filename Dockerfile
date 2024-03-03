FROM python:3.12.2-bullseye

VOLUME /src
WORKDIR /src

COPY src src
COPY pyproject.toml pyproject.toml
COPY README.md README.md

# Also install pyallel so we can copy it's metadata when running pyinstaller
RUN pip install pyinstaller==6.4.0 .

CMD [ "pyinstaller", "--onefile", "--exclude-module", "PyInstaller", "--copy-metadata", "pyallel", "--name", "pyallel-0.18.5-linux-x86_64", "./src/pyallel/main.py" ]

