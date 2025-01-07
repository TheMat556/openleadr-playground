import os
import sys
import subprocess
import logging

logging.basicConfig(
  level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s'
)


def main(filename):
  if not os.path.isfile(filename):
    return

  result = subprocess.run(['git', 'diff', '--quiet', filename], capture_output=True)
  if result.returncode != 0:
    logging.warning(
      f'Warning: {filename} contains uncommitted changes. Please commit or stash changes before proceeding.'
    )
    sys.exit(1)

  if not os.access(filename, os.W_OK):
    logging.error(f'Error: No write permission for {filename}')
    sys.exit(1)

  try:
    os.remove(filename)
    logging.info(f'Successfully removed generated file: {filename}')
  except OSError as e:
    logging.error(f'Failed to remove {filename}: {e}')
    sys.exit(1)


if __name__ == '__main__':
  if len(sys.argv) != 2:
    logging.error('Error: Expected exactly one argument (filename)')
    logging.info('Usage: python delete_generated_file.py <filename>')
    sys.exit(1)

  filename = sys.argv[1]
  if not all(c.isalnum() or c in '._-' for c in filename):
    logging.error('Error: Filename contains invalid characters')
    sys.exit(1)

  main(filename)
