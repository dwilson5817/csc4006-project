#!/usr/bin/env sh

# usage: ./fsUp.sh working_dir

WORKING_DIR=$1

fusermount -uz "$WORKING_DIR/mount"
