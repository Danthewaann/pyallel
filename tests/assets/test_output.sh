#!/usr/bin/env bash

echo "running a command..."
sleep 1
echo "this is a very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very long line"
echo -n "this line contains..."
sleep 1
echo "some delayed output"
sleep 1
for i in {1..20}; do
	echo "line $i"
	sleep 0.1
done
sleep 1
echo "bye!"
