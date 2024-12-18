#!/usr/bin/env bash

trap "echo received signal! && sleep 1" SIGINT SIGTERM

echo "running a command..."
sleep 1
echo -n "this is a "
for i in {1..100}; do
	echo -n "very "
done
echo "long line"
echo -n "this line contains..."
sleep 1
echo "some delayed output"
sleep 1
for i in {1..25}; do
	echo "line $i"
	sleep 0.1
done
sleep 1
echo "bye!"
