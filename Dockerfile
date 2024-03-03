FROM python:3.12.2-bullseye

VOLUME /src
WORKDIR /src

COPY src src
COPY pyproject.toml pyproject.toml
COPY README.md README.md

# Also install pyallel so we can copy it's metadata when running pyinstaller
RUN pip install pyinstaller==6.4.0 .

CMD [ "./build.sh" ]

