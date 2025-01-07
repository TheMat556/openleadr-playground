import os
import sys
import subprocess


def main(filename):
  if not os.path.isfile(filename):
    return

  result = subprocess.run(['git', 'diff', '--quiet', filename], capture_output=True)
  if result.returncode != 0:
    print(
      f'Warning: {filename} contains uncommitted changes. Please commit or stash changes before proceeding.'
    )
    sys.exit(1)

  if not os.access(filename, os.W_OK):
    print(f'Error: No write permission for {filename}')
    sys.exit(1)

  try:
    os.remove(filename)
    print(f'Removed generated {filename}')
  except OSError as e:
    print(f'Error: Failed to remove {filename}: {e}')
    sys.exit(1)


if __name__ == '__main__':
  if len(sys.argv) != 2:
    print('Error: Expected exactly one argument (filename)')
    print('Usage: python delete_generated_file.py <filename>')
    sys.exit(1)

  filename = sys.argv[1]
  if not all(c.isalnum() or c in '._-' for c in filename):
    print('Error: Filename contains invalid characters')
    sys.exit(1)

  main(filename)
