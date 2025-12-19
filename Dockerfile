ARG arch
FROM --platform=linux/${arch} python:3.13-bullseye

ARG uid=
ARG gid=

VOLUME /src
WORKDIR /src

# Setup a build user
RUN addgroup --system build --gid 1000 && adduser --system build --uid ${uid} --gid 1000

COPY src src
COPY pyproject.toml pyproject.toml
COPY README.md README.md

# Also install pyallel so we can copy it's metadata when running pyinstaller
RUN pip install . --group dev

# Switch to the build user before running the build scripts
USER build

ENV arch ${arch}
CMD [ "./build.sh", "linux" ]

