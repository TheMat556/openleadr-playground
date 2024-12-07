import argparse
import os


def main():
    parser = argparse.ArgumentParser(description='Process some arguments.')
    parser.add_argument('name', type=str, help='A name to greet')
    args = parser.parse_args()

    vtn_name = os.getenv('VTN_NAME')
    ven_name = os.getenv('VEN_NAME')
    path_prefix = os.getenv('PATH_PREFIX')

    print(f'Hi, {args.name}')
    print(f'VTN_NAME: {vtn_name}')
    print(f'VEN_NAME: {ven_name}')
    print(f'PATH_PREFIX: {path_prefix}')

if __name__ == '__main__':
    main()
