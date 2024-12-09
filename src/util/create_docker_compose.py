import yaml
import argparse
import sys
import json

def generate_node(layer, index, max_layers, parent_path_prefix=None, base_port=8080, port_increment=0, gradio_port=7862, parent_ports=None):
    """
    Generate a node with the given layer and index.
    """
    if layer >= max_layers:
        return None

    path_prefix = '/' + '/'.join(index.split('_')) + '/'
    environment = {
        'VTN_NAME': f'vtn_{index}',
        'VTN_URL': f'http://0.0.0.0:{base_port}{path_prefix}OpenADR2/Simple/2.0b',
        'VTN_PATH_PREFIX': f'{path_prefix}OpenADR2/Simple/2.0b',
        'VEN_NAME': f'ven_{index}',
        'GRADIO_PORT': '7862',
        'GRADIO_SERVER_NAME': '0.0.0.0'
    }
    if parent_path_prefix is not None:
        parent_port = parent_ports[0].split(':')[0]
        environment['CONNECT_VTN_URL'] = f'http://0.0.0.0:{parent_port}{parent_path_prefix}OpenADR2/Simple/2.0b'

    port = base_port + port_increment
    port_mapping = [f'{port}:8080', f'{gradio_port}:{7862}']

    # Determine the Dockerfile based on the node's index
    if index == "0":
        dockerfile = './src/docker/top_node/Dockerfile'
    elif layer == max_layers - 1:
        dockerfile = './src/docker/bottom_node/Dockerfile'
    else:
        dockerfile = './src/docker/middle_node/Dockerfile'

    node = {
        'path_prefix': path_prefix,
        'server_name': index,
        'build': {
            'context': '.',
            'dockerfile': dockerfile
        },
        'container_name': f'{index}_container',
        'environment': environment,
        'ports': port_mapping,
        'networks': ['my_network'],
        'depends_on': []
    }

    children = []
    for i in range(2):
        child_index = f"{index}_{i}" if index != "0" else f"{index}_{i}"
        child_node = generate_node(layer + 1, child_index, max_layers, path_prefix, base_port, port_increment + len(children) + 1, gradio_port + len(children) + 1, port_mapping)
        if child_node:
            children.append(child_node)
            child_node['depends_on'].append(index)

    if children:
        node['children'] = children

    return node

def flatten_services(node, services, env_json):
    """
    Flatten the hierarchical structure into a dictionary of services and build the environment JSON structure.
    """
    service_name = node['server_name']
    services[service_name] = {
        'build': node['build'],
        'container_name': node['container_name'],
        'environment': [f'{key}={value}' for key, value in node['environment'].items()],
        'ports': node['ports'],
        'networks': node['networks'],
        'depends_on': node['depends_on']
    }
    rest_api_port = node['ports'][0].split(':')[0]
    env_json[node['container_name']] = {**node['environment'], 'REST_API_PORT': rest_api_port}
    if 'children' in node:
        for child in node['children']:
            flatten_services(child, services, env_json)

def create_docker_compose(layers):
    """
    Generate the hierarchical YAML structure and create docker-compose.yml.
    """
    root = generate_node(0, "0", layers)
    services = {}
    env_json = {}
    flatten_services(root, services, env_json)

    compose_content = {
        'version': '3.8',
        'services': services,
        'networks': {
            'my_network': {
                'driver': 'bridge'
            }
        }
    }

    with open('docker-compose.yml', 'w') as file:
        yaml.dump(compose_content, file, default_flow_style=False, Dumper=CustomDumper)

    with open('env_variables.json', 'w') as file:
        json.dump(env_json, file, indent=2)

class CustomDumper(yaml.SafeDumper):
    def represent_scalar(self, tag, value, style=None):
        if tag == 'tag:yaml.org,2002:str' and ':' in value and 'http' not in value:
            return super().represent_scalar(tag, value, style='"')
        return super().represent_scalar(tag, value, style)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate docker-compose.yml with a specified number of layers.')
    parser.add_argument('layers', type=int, nargs='?', help='Number of layers to generate')
    args = parser.parse_args()

    if args.layers is None:
        print("Error: Number of layers must be specified.")
        sys.exit(1)

    create_docker_compose(args.layers)
