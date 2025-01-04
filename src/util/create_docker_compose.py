import logging

import ruamel.yaml
import argparse
import sys
import json
from ruamel.yaml.scalarstring import SingleQuotedScalarString
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
import os

# Set up logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Load environment variables from .env.mqtt file
load_dotenv('.env.mqtt')

# Create YAML instance with specific string handling
yaml = ruamel.yaml.YAML()
yaml.preserve_quotes = True  # Preserve existing quotes
yaml.default_flow_style = False  # Use block style
yaml.allow_unicode = True  # Allow Unicode characters
MQTT_CONFIG_WRITTEN = False

# Validate MQTT environment variables
required_mqtt_vars = [
  'PRIVATE_MQTT_BROKER_URL',
  'PRIVATE_MQTT_USERNAME',
  'PRIVATE_MQTT_PASSWORD',
  'PRIVATE_MQTT_PORT',
]


class PortRegistry:
  def __init__(self):
    self.used_ports = set()

  def allocate_port(self, base_port: int) -> int:
    if not 0 <= base_port <= 65535:
      raise ValueError(f'Invalid port number: {base_port}')
    port = base_port
    while port in self.used_ports:
      port += 1
    if port > 65535:
      raise ValueError('No available ports in valid range')
    self.used_ports.add(port)
    return port


class IPAllocator:
  def __init__(self, base_ip: str = '172.18.0'):
    try:
      octets = base_ip.split('.')
      if len(octets) != 3 or not all(
        o.isdigit() and 0 <= int(o) <= 255 for o in octets
      ):
        raise ValueError
    except (ValueError, AttributeError):
      raise ValueError(
        f'Invalid base_ip format: {base_ip}. Expected format: xxx.xxx.xxx'
      )
    self.base_ip = base_ip
    self.used_ips = set()
    self.available_count = 253

  def allocate_ip(self) -> str:
    if self.available_count <= 0:
      raise ValueError('IP address pool exhausted')
    for i in range(2, 255):
      ip = f'{self.base_ip}.{i}'
      if ip not in self.used_ips:
        self.used_ips.add(ip)
        self.available_count -= 1
        return ip
    raise ValueError('IP address pool fragmented')


def generate_node(
  layer: int,
  index: str,
  max_layers: int,
  port_registry: PortRegistry,
  ip_allocator: IPAllocator,
  parent_path_prefix: Optional[str] = None,
  base_port: int = 8080,
  gradio_port: int = 7862,
  rest_api_port: int = 5000,
  parent_ports: Optional[List[str]] = None,
  parent_service_name: Optional[str] = None,
  parent_ip: Optional[str] = None,
  last_layer_children: int = 2,
) -> Optional[Dict[str, Any]]:
  global MQTT_CONFIG_WRITTEN

  if layer >= max_layers:
    return None

  port = port_registry.allocate_port(base_port)
  gradio_port = port_registry.allocate_port(gradio_port)
  rest_api_port = port_registry.allocate_port(rest_api_port)
  ip_address = ip_allocator.allocate_ip()

  path_prefix = '/' + '/'.join(index.split('_')) + '/'
  environment = {
    'NODE_ID': index,
    'VTN_NAME': f'vtn_{index}',
    'VTN_URL': f'http://localhost:{port}{path_prefix}OpenADR2/Simple/2.0b',
    'VTN_PATH_PREFIX': f'{path_prefix}OpenADR2/Simple/2.0b',
    'VEN_NAME': f'ven_{index}',
    'GRADIO_PORT': str(gradio_port),
    'GRADIO_SERVER_NAME': '0.0.0.0',
    'REST_API_PORT': str(rest_api_port),
    'VTN_PORT': str(port),
    'VTN_SELF_HOST': f'http://{ip_address}',
    'LAYER': str(layer),
  }
  if parent_path_prefix and parent_service_name and parent_ip:
    parent_port = parent_ports[0].split(':')[0]
    environment['CONNECT_VTN_URL'] = (
      f'http://{parent_ip}:{parent_port}{parent_path_prefix}OpenADR2/Simple/2.0b'
    )

  missing_vars = [var for var in required_mqtt_vars if not os.getenv(var)]
  if missing_vars:
    logger.warning(
      f"Missing required MQTT environment variables: {', '.join(missing_vars)}"
    )
    raise ValueError(
      'Required MQTT environment variables are missing. Please check .env.mqtt file'
    )

  # Update environment with MQTT configuration if all variables are present
  if layer == max_layers - 1 and not MQTT_CONFIG_WRITTEN:
    MQTT_CONFIG_WRITTEN = True
    environment.update(
      {
        'PRIVATE_MQTT_BROKER_URL': os.getenv('PRIVATE_MQTT_BROKER_URL'),
        'PRIVATE_MQTT_USERNAME': os.getenv('PRIVATE_MQTT_USERNAME'),
        'PRIVATE_MQTT_PASSWORD': os.getenv('PRIVATE_MQTT_PASSWORD'),
        'PRIVATE_MQTT_PORT': os.getenv('PRIVATE_MQTT_PORT'),
        'PRIVATE_MQTT_TOPIC_LOAD_PROFILE': os.getenv('PRIVATE_MQTT_TOPIC_LOAD_PROFILE'),
        'PRIVATE_MQTT_TOPIC_LOAD_CONSUMPTION': os.getenv(
          'PRIVATE_MQTT_TOPIC_LOAD_CONSUMPTION'
        ),
      }
    )

  port_mapping = [
    SingleQuotedScalarString(f'{port}:{port}'),
    SingleQuotedScalarString(f'{gradio_port}:{gradio_port}'),
    SingleQuotedScalarString(f'{rest_api_port}:{rest_api_port}'),
  ]

  if index == '0':
    dockerfile = './src/docker/top_node/Dockerfile'
  elif layer == max_layers - 1:
    dockerfile = './src/docker/bottom_node/Dockerfile'
  else:
    dockerfile = './src/docker/middle_node/Dockerfile'

  node = {
    'path_prefix': path_prefix,
    'server_name': index,
    'build': {'context': '.', 'dockerfile': dockerfile},
    'container_name': f'{index}_container',
    'environment': environment,
    'ports': port_mapping,
    'networks': {'my_network': {'ipv4_address': ip_address}},
    'depends_on': {},
    'expose': [port, rest_api_port],
  }

  if layer < max_layers - 1:
    node['healthcheck'] = {
      'test': SingleQuotedScalarString(
        f"curl -f -s -o /dev/null -w '%{{http_code}}' 127.0.0.1:{port}{path_prefix}OpenADR2/Simple/2.0b | grep 404 || exit 1"
      ),
      'interval': '30s',
      'timeout': '10s',
      'retries': 10,
    }

  children = []
  num_children = last_layer_children
  for i in range(num_children):
    child_index = f'{index}_{i}'
    child_node = generate_node(
      layer + 1,
      child_index,
      max_layers,
      port_registry,
      ip_allocator,
      path_prefix,
      base_port + 1,
      gradio_port + 1,
      rest_api_port + 1,
      port_mapping,
      f'{index}_node',
      ip_address,
      last_layer_children,
    )
    if child_node:
      children.append(child_node)
      child_node['depends_on'][index] = {'condition': 'service_healthy'}

  if children:
    node['children'] = children

  return node


def flatten_services(
  node: Dict[str, Any], services: Dict[str, Any], env_json: Dict[str, Any]
) -> None:
  service_name = node['server_name']

  from ruamel.yaml.comments import CommentedSeq

  ports = CommentedSeq()
  for port in node['ports']:
    ports.append(port)

  services[service_name] = {
    'build': node['build'],
    'container_name': node['container_name'],
    'environment': [f'{key}={value}' for key, value in node['environment'].items()],
    'ports': ports,
    'networks': node['networks'],
    'depends_on': node['depends_on'],
    'expose': node['expose'],
  }
  if 'healthcheck' in node:
    services[service_name]['healthcheck'] = node['healthcheck']

  env_json[node['container_name']] = {**node['environment']}
  if 'children' in node:
    for child in node['children']:
      flatten_services(child, services, env_json)


def create_docker_compose(layers: int, last_layer_children: int) -> None:
  if not isinstance(layers, int):
    raise TypeError('layers must be an integer')
  if layers <= 0:
    raise ValueError('layers must be positive')
  if layers > 10:
    raise ValueError('layers exceeds maximum allowed value')

  port_registry = PortRegistry()
  ip_allocator = IPAllocator()
  root = generate_node(
    0, '0', layers, port_registry, ip_allocator, last_layer_children=last_layer_children
  )
  services = {}
  env_json = {}
  flatten_services(root, services, env_json)

  services['node_dashboard'] = {
    'build': {'context': '.', 'dockerfile': './src/docker/node_dashboard/Dockerfile'},
    'container_name': 'node_dashboard',
    'ports': [SingleQuotedScalarString('7860:7860')],
    'networks': {'my_network': {'ipv4_address': ip_allocator.allocate_ip()}},
    'environment': ['NODE_GRADIO_PORT=7860'],
  }

  compose_content = {
    'version': '3.8',
    'services': services,
    'networks': {
      'my_network': {
        'driver': 'bridge',
        'ipam': {'config': [{'subnet': '172.18.0.0/16'}]},
      }
    },
  }

  try:
    with open('docker-compose.yml', 'w') as file:
      yaml.dump(compose_content, file)
    with open('env_variables.json', 'w') as file:
      json.dump(env_json, file, indent=2)
  except (IOError, PermissionError) as e:
    print(f'Error writing configuration files: {e}')
    sys.exit(1)


if __name__ == '__main__':
  parser = argparse.ArgumentParser(
    description='Generate docker-compose.yml with a specified number of layers and children in the last layer.'
  )
  parser.add_argument(
    '-l', '--layers', type=int, required=True, help='Number of layers to generate'
  )
  parser.add_argument(
    '-c',
    '--children',
    type=int,
    required=True,
    help='Number of children in the last layer',
  )
  args = parser.parse_args()

  create_docker_compose(args.layers, args.children)
