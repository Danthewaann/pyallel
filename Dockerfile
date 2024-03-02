FROM python:3.12.1-bullseye

RUN pip install pyinstaller

COPY src src

CMD ["pyinstaller", "--onefile", "--name", "pyallel-0.18.4-linux-amd64", "--distpath", "/dist", "./src/pyallel/main.py"]

