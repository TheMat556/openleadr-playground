import logging
import subprocess
import sys

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

  staged_files = result.stdout.lower().splitlines()
  if '.env.mqtt' in staged_files:
    logging.info(
      '.env.mqtt file is staged for commit. Please remove it before pushing.'
    )
    sys.exit(1)


if __name__ == '__main__':
  main()
