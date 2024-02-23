#!/usr/bin/env bash

trap "echo ignore! && sleep 1" SIGINT SIGTERM

echo "hi"
sleep 1
echo "bye"
