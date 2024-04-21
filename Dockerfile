ARG arch
FROM --platform=linux/${arch} python:3.12.2-bullseye

ARG uid=
ARG gid=

VOLUME /src
WORKDIR /src

# Setup a build user
RUN addgroup build --gid ${gid} && adduser --system build --uid ${uid} --gid ${gid}

COPY src src
COPY pyproject.toml pyproject.toml
COPY README.md README.md
COPY requirements_build.txt requirements_build.txt

# Also install pyallel so we can copy it's metadata when running pyinstaller
RUN pip install . -r requirements_build.txt

# Switch to the build user before running the build scripts
USER build

ENV arch ${arch}
CMD [ "./build.sh", "linux" ]

