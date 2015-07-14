#!/bin/bash -e
autoreconf -ivf
./configure
find . -name "*.py" -exec pyflakes {} \+
find . -name "*.py" -exec pep8 {} \+
