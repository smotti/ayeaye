#!/bin/bash

echo "Start test VM"
vagrant up --provision

echo "Run tests"
for t in tests/test_*.py; do
  python3 $t
done

echo "Destroy test VM"
vagrant destroy -f
