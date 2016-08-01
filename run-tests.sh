#!/bin/bash

for t in tests/test_*.py; do
  python $t
done
