#!/usr/bin/env bash

trap "echo ignore! && sleep 1" SIGINT

echo "hi"
sleep 1
echo "bye"
