import argparse


def main():
  parser = argparse.ArgumentParser(description='Process some arguments.')
  parser.add_argument('name', type=str, help='A name to greet')
  args = parser.parse_args()

  print(f'Hi, {args.name}')


if __name__ == '__main__':
  main()
