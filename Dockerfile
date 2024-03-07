ARG arch
FROM --platform=linux/${arch} python:3.12.2-bullseye

VOLUME /src
WORKDIR /src

COPY src src
COPY pyproject.toml pyproject.toml
COPY README.md README.md
COPY requirements_build.txt requirements_build.txt

# Also install pyallel so we can copy it's metadata when running pyinstaller
RUN pip install . -r requirements_build.txt

ENV arch ${arch}
CMD [ "./build.sh", "linux" ]

