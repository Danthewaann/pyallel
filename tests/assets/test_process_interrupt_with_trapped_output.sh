#!/usr/bin/env bash

trap "echo error && exit 2" SIGINT SIGTERM

echo "hi"
sleep 1
