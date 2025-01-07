import os
import subprocess
import logging

logging.basicConfig(
  level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s'
)


def main():
  result = subprocess.run(
    ['git', 'diff', '--cached', '--name-only'],
    capture_output=True,
    text=True,
    check=True,
  )
  if not result.stdout:
    return

  staged_files = result.stdout.splitlines()
  for file in staged_files:
    if file.endswith('slider_values.txt'):
      # Prevent path traversal
      clean_filename = os.path.basename(file)
      if file != clean_filename:
        logging.error(f'Error: Invalid path in filename {file}')
        continue

      # Check for write permissions
      if not os.access(file, os.W_OK):
        logging.error(f'Error: No write permission for {file}')
        continue

      # Check for uncommitted changes
      try:
        result = subprocess.run(
          ['git', 'diff', '--quiet', file], capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
          logging.warning(f'Warning: {file} contains uncommitted changes')
          continue
      except FileNotFoundError:
        logging.warning('Git is not installed. Skipping git diff check.')

      try:
        os.remove(file)
        logging.info(f'Successfully removed {file}')
      except OSError as e:
        logging.error(f'Failed to remove {file}: {e}')


if __name__ == '__main__':
  main()
