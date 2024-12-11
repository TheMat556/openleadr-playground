import ruamel.yaml
import argparse
import sys
import json
from ruamel.yaml.scalarstring import SingleQuotedScalarString

# Create YAML instance with specific string handling
yaml = ruamel.yaml.YAML()
yaml.preserve_quotes = True  # Preserve existing quotes
yaml.default_flow_style = False  # Use block style
yaml.allow_unicode = True


class PortRegistry:
  def __init__(self):
    self.used_ports = set()

  def allocate_port(self, base_port):
    port = base_port
    while port in self.used_ports:
      port += 1
    self.used_ports.add(port)
    return port


class IPAllocator:
  def __init__(self, base_ip='172.18.0'):
    self.base_ip = base_ip
    self.used_ips = set()

  def allocate_ip(self):
    for i in range(2, 255):  # Start from .2, avoid .0 and .1
      ip = f'{self.base_ip}.{i}'
      if ip not in self.used_ips:
        self.used_ips.add(ip)
        return ip
    raise ValueError('No available IP addresses')


def generate_node(
  layer,
  index,
  max_layers,
  port_registry,
  ip_allocator,
  parent_path_prefix=None,
  base_port=8080,
  gradio_port=7862,
  rest_api_port=5000,
  parent_ports=None,
  parent_ip=None,
):
  """
  Generate a node with the given layer and index.
  """
  if layer >= max_layers:
    return None

  port = port_registry.allocate_port(base_port)
  gradio_port = port_registry.allocate_port(gradio_port)
  rest_api_port = port_registry.allocate_port(rest_api_port)

  path_prefix = '/' + '/'.join(index.split('_')) + '/'
  environment = {
    'VTN_NAME': f'vtn_{index}',
    'VTN_URL': f'http://0:{base_port}{path_prefix}OpenADR2/Simple/2.0b',
    'VTN_PATH_PREFIX': f'{path_prefix}OpenADR2/Simple/2.0b',
    'VEN_NAME': f'ven_{index}',
    'GRADIO_PORT': str(gradio_port),
    'GRADIO_SERVER_NAME': '0.0.0.0',
    'REST_API_PORT': str(rest_api_port),
  }
  if parent_path_prefix is not None and parent_ip is not None:
    parent_port = parent_ports[0].split(':')[0]
    environment['CONNECT_VTN_URL'] = (
      f'http://{parent_ip}:{parent_port}{parent_path_prefix}OpenADR2/Simple/2.0b'
    )

  port_mapping = [
    SingleQuotedScalarString(f'{port}:{port}'),
    SingleQuotedScalarString(f'{gradio_port}:{gradio_port}'),
    SingleQuotedScalarString(f'{rest_api_port}:{rest_api_port}'),
  ]
  ipv4_address = ip_allocator.allocate_ip()

  # Determine the Dockerfile based on the node's index
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
    'networks': {'my_network': {'ipv4_address': ipv4_address}},
    'depends_on': {},
    'expose': [port],
  }

  if layer < max_layers - 1:
    node['healthcheck'] = {
      'test': SingleQuotedScalarString(
        f"curl -f -s -o /dev/null -w '%{{http_code}}' 127.0.0.1:{port}{path_prefix}OpenADR2/Simple/2.0b | grep 404 || exit 1"
      ),
      'interval': '30s',
      'timeout': '10s',
      'retries': 5,
    }

  children = []
  for i in range(2):
    child_index = f'{index}_{i}' if index != '0' else f'{index}_{i}'
    child_node = generate_node(
      layer + 1,
      child_index,
      max_layers,
      port_registry,
      ip_allocator,
      path_prefix,
      base_port + 1,  # Increment base_port for each child node
      gradio_port + 1,  # Increment gradio_port for each child node
      rest_api_port + 1,  # Increment rest_api_port for each child node
      port_mapping,
      ipv4_address,
    )
    if child_node:
      children.append(child_node)
      child_node['depends_on'][index] = {'condition': 'service_healthy'}

  if children:
    node['children'] = children

  return node


def flatten_services(node, services, env_json):
  """
  Flatten the hierarchical structure into a dictionary of services and build the environment JSON structure.
  """
  service_name = node['server_name']

  # Use CommentedSeq to precisely control port string representation
  from ruamel.yaml.comments import CommentedSeq

  ports = CommentedSeq()
  for port in node['ports']:
    ports.append(port)

  services[service_name] = {
    'build': node['build'],
    'container_name': node['container_name'],
    'environment': [f'{key}={value}' for key, value in node['environment'].items()],
    'ports': ports,  # Use CommentedSeq to preserve exact port string representation
    'networks': node['networks'],
    'depends_on': node['depends_on'],
    'expose': node['expose'],
  }
  if 'healthcheck' in node:
    services[service_name]['healthcheck'] = node['healthcheck']

  adr_mapping_port = node['ports'][0].split(':')[0]
  env_json[node['container_name']] = {
    **node['environment'],
    'ADR_MAPPING_PORT': adr_mapping_port,
  }
  if 'children' in node:
    for child in node['children']:
      flatten_services(child, services, env_json)


def create_docker_compose(layers):
  """
  Generate the hierarchical YAML structure and create docker-compose.yml.
  """
  port_registry = PortRegistry()
  ip_allocator = IPAllocator()
  root = generate_node(0, '0', layers, port_registry, ip_allocator)
  services = {}
  env_json = {}
  flatten_services(root, services, env_json)

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
    description='Generate docker-compose.yml with a specified number of layers.'
  )
  parser.add_argument(
    'layers', type=int, nargs='?', help='Number of layers to generate'
  )
  args = parser.parse_args()

  if args.layers is None:
    print('Error: Number of layers must be specified.')
    sys.exit(1)

  create_docker_compose(args.layers)
