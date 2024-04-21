#!/bin/sh

rm -rf build dist specs

# Generic linux
echo "### BUILDING GENERIC LINUX - x86_64 ###"
echo
docker build --tag pyallel --build-arg 'arch=x86_64' --build-arg "uid=$(id -u)" --build-arg "gid=$(id -g)" . && \
    docker run -e 'arch=x86_64' --rm --volume "$(pwd):/src" pyallel
echo
echo "### BUILDING GENERIC LINUX - aarch64 ###"
echo
docker build --tag pyallel --build-arg 'arch=aarch64' --build-arg "uid=$(id -u)" --build-arg "gid=$(id -g)" . && \
    docker run -e 'arch=aarch64' --rm --volume "$(pwd):/src" pyallel
echo
echo "### DONE GENERIC LINUX ###"

# Alpine linux
echo "### BUILDING ALPINE LINUX - x86_64 ###"
echo
docker build --tag pyallel-alpine --build-arg 'arch=x86_64' --build-arg "uid=$(id -u)" --build-arg "gid=$(id -g)" --file Dockerfile.alpine . && \
    docker run -e 'arch=x86_64' --rm --volume "$(pwd):/src" pyallel-alpine
echo
echo "### BUILDING ALPINE LINUX - aarch64 ###"
echo
docker build --tag pyallel-alpine --build-arg 'arch=aarch64' --build-arg "uid=$(id -u)" --build-arg "gid=$(id -g)" --file Dockerfile.alpine . && \
    docker run -e 'arch=aarch64' --rm --volume "$(pwd):/src" pyallel-alpine
echo
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
echo
python -m venv .venv && \
    . .venv/bin/activate && \
    pip install . -r requirements_build.txt && \
    ./build.sh "$distro" "$arch"
echo
echo "### DONE LOCAL ###"
