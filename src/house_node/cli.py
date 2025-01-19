import argparse
import asyncio
from dotenv import load_dotenv

from src.house_node.config.house_node_config import HouseNodeConfig
from .house_node import HouseNode


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description='Run a house node')
  parser.add_argument('--node-id', required=True)
  parser.add_argument('--ven-name', required=True)
  parser.add_argument('--vtn-name', required=True)
  parser.add_argument('--vtn-url', required=True)
  parser.add_argument('--openadr-host', default='localhost')
  parser.add_argument('--openadr-port', type=int, default=8080)
  parser.add_argument('--openadr-path', default='/OpenADR2/Simple/2.0b')
  parser.add_argument('--rest-port', type=int, default=5000)
  return parser.parse_args()


async def main() -> None:
  load_dotenv()
  args = parse_args()

  config = HouseNodeConfig(
    node_id=args.node_id,
    ven_name=args.ven_name,
    vtn_name=args.vtn_name,
    vtn_url=args.vtn_url,
    openadr_http_host=args.openadr_host,
    openadr_http_port=args.openadr_port,
    openadr_vtn_path_prefix=args.openadr_path,
    rest_api_port=args.rest_port,
  )

  node = HouseNode(config)
  await node.run()


if __name__ == '__main__':
  asyncio.run(main())
