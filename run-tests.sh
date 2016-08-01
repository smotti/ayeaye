#!/bin/bash

for t in tests/test_*.py; do
  python3 $t
done
