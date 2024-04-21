#!/bin/sh

# Generic linux
echo "### BUILDING GENERIC LINUX ###"
docker build --tag pyallel --build-arg 'arch=x86_64' . && \
    docker run -e 'arch=x86_64' --rm --volume "$(pwd):/src" pyallel
docker build --tag pyallel --build-arg 'arch=aarch64' . && \
    docker run -e 'arch=aarch64' --rm --volume "$(pwd):/src" pyallel
echo "### DONE GENERIC LINUX ###"

# Alpine linux
echo "### BUILDING ALPINE LINUX ###"
docker build --tag pyallel-alpine --build-arg 'arch=x86_64' --file Dockerfile.alpine . && \
    docker run -e 'arch=x86_64' --rm --volume "$(pwd):/src" pyallel-alpine
docker build --tag pyallel-alpine --build-arg 'arch=aarch64' --file Dockerfile.alpine . && \
    docker run -e 'arch=aarch64' --rm --volume "$(pwd):/src" pyallel-alpine
echo "### DONE ALPINE LINUX ###"

# Local OS
distro=$(uname | tr '[:upper:]' '[:lower:]')
arch=$(uname -m)

if [ "$arch" = "arm64" ]; then
    arch="aarch64"
elif [ "$arch" = "x86_64" ]; then
    arch="x86_64"
else
    arch=unknown
fi

echo "### BUILDING LOCAL ###"
python -m venv .venv && \
    . .venv/bin/activate && \
    pip install . -r requirements_build.txt && \
    ./build.sh "$distro" "$arch"
echo "### DONE LOCAL ###"
