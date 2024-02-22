#!/usr/bin/env bash

trap "echo error && exit 2" SIGINT

echo "hi"
sleep 1
