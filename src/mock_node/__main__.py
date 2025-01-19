import asyncio
import os
from dotenv import load_dotenv
from src.mock_node.config import MockNodeConfig
from src.mock_node.mock_node import MockNode


async def main() -> None:
  load_dotenv()

  config = MockNodeConfig(
    node_id=os.getenv('NODE_ID'),
    vtn_name=os.getenv('VTN_NAME', 'default_vtn'),
    openadr_http_host=os.getenv('VTN_URL', '127.0.0.1'),
    openadr_http_port=int(os.getenv('OPENADR_HTTP_PORT', 8080)),
    openadr_vtn_path_prefix=os.getenv('VTN_PATH_PREFIX', '/0/OpenADR2/Simple/2.0b'),
    rest_api_port=int(os.getenv('REST_API_PORT', 5000)),
    gradio_port=int(os.getenv('GRADIO_PORT', 7860)),
    gradio_host=os.getenv('GRADIO_SERVER_NAME', '0.0.0.0'),
  )

  node = MockNode(config)
  await node.run()


if __name__ == '__main__':
  asyncio.run(main())
