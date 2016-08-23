#!/bin/bash

export PYTHONPATH=$PYTHONPATH:$(pwd)

echo "Start test VM"
vagrant up --provision

echo "Run tests"
for t in ayeaye/tests/test_*.py; do
  python3 $t
done

#echo "Destroy test VM"
#vagrant destroy -f

echo "Suspend test VM"
vagrant suspend
