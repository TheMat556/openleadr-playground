import subprocess
import sys


def main():
  result = subprocess.run(
    ['git', 'diff', '--cached', '--name-only'], capture_output=True, text=True
  )
  if '.env.mqtt' in result.stdout.splitlines():
    print('.env.mqtt file is staged for commit. Please remove it before pushing.')
    sys.exit(1)


if __name__ == '__main__':
  main()
