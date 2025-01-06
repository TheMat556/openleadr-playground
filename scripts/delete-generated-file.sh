#!/bin/bash
set -e  # Exit on error
if [ "$#" -ne 1 ]; then
    echo "Error: Expected exactly one argument (filename)"
    echo "Usage: $0 <filename>"
    exit 1
fi
if [[ ! "$1" =~ ^[a-zA-Z0-9._-]+$ ]]; then
    echo "Error: Filename contains invalid characters"
    exit 1
fi

filename="$1"
  if ! git rev-parse --git-dir > /dev/null 2>&1; then
      echo "Error: Not in a git repository"
      exit 1
  fi
  if [ -f "$filename" ]; then
      if ! git diff --quiet "$filename" 2>/dev/null; then
          echo "Warning: $filename contains uncommitted changes. Please commit or stash changes before proceeding."
          exit 1
      fi

      if [ ! -w "$filename" ]; then
          echo "Error: No write permission for $filename"
          exit 1
      fi

      if rm "$filename"; then
          echo "Removed generated $filename"
      else
          echo "Error: Failed to remove $filename"
          exit 1
      fi
fi
