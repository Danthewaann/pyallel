#!/bin/sh

rm -rf build dist specs

user_id=$(id -u)
group_id=$(id -g)
cur_dir=$(pwd)

# Local OS setup
distro=$(uname | tr '[:upper:]' '[:lower:]')
arch=$(uname -m)

if [ "$arch" = "arm64" ]; then
    arch="aarch64"
elif [ "$arch" = "x86_64" ]; then
    arch="x86_64"
else
    arch=unknown
fi

poetry install

poetry run pyallel "docker build --tag pyallel-x86_64 --build-arg 'arch=x86_64' --build-arg 'uid=$user_id' --build-arg 'gid=$group_id' . && docker run -e 'arch=x86_64' --rm --volume '$cur_dir:/src' pyallel-x86_64" \
        "docker build --tag pyallel-aarch64 --build-arg 'arch=aarch64' --build-arg 'uid=$user_id' --build-arg 'gid=$group_id' . && docker run -e 'arch=aarch64' --rm --volume '$cur_dir:/src' pyallel-aarch64" \
        "docker build --tag pyallel-x86_64-alpine --build-arg 'arch=x86_64' --build-arg 'uid=$user_id' --build-arg 'gid=$group_id' --file Dockerfile.alpine . && docker run -e 'arch=x86_64' --rm --volume '$cur_dir:/src' pyallel-x86_64-alpine" \
        "docker build --tag pyallel-aarch64-alpine --build-arg 'arch=aarch64' --build-arg 'uid=$user_id' --build-arg 'gid=$group_id' --file Dockerfile.alpine . && docker run -e 'arch=aarch64' --rm --volume '$cur_dir:/src' pyallel-aarch64-alpine" \
        ::: \
        "poetry run ./build.sh $distro $arch"
