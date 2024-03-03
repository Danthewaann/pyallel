FROM python:3.12.1-bullseye

COPY src src
COPY pyproject.toml pyproject.toml
COPY README.md README.md

# Also install pyallel so we can copy it's metadata when running pyinstaller
RUN pip install pyinstaller .

CMD [ "pyinstaller", "--onefile", "--copy-metadata", "pyallel", "--name", "pyallel-0.18.4-linux-x86_64", "--distpath", "/dist", "./src/pyallel/main.py" ]

