#!/bin/sh

# Include parent dir in PATH to pick up the main lib in import path.
#PATH=$PATH:../flickrsync ./test.py 2> ./test.log

../bin/flickrsync.py --path=./pics1-orig --album=test-sync --push --checksum --loglevel=INFO --logfile=./flickrsync-bin-test.log
