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
      try:
        os.remove(file)
        logging.info(f'Successfully removed {file}')
      except OSError as e:
        logging.error(f'Failed to remove {file}: {e}')


if __name__ == '__main__':
  main()
