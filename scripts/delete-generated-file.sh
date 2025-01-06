#!/bin/bash
filename="$1"
if [ -f "$filename" ]; then
    if git diff --quiet "$filename"; then
        rm "$filename" && echo "Removed generated $filename"
    else
        echo "Warning: $filename contains uncommitted changes. Please commit or stash changes before proceeding."
        exit 1
    fi
fi
