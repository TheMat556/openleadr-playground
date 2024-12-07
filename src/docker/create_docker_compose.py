import yaml

def generate_node(layer, index, max_layers, parent_path_prefix=None):
    """
    Generate a node with the given layer and index.
    """
    if layer >= max_layers:
        return None

    path_prefix = '/' + '/'.join(index.split('_'))
    environment = [
        f'VTN_NAME=vtn_{index}',
        f'VEN_NAME=ven_{index}',
        f'PATH_PREFIX={path_prefix}'
    ]
    if parent_path_prefix is not None:
        environment.append(f'CONNECT_VTN_PREFIX={parent_path_prefix}')

    node = {
        'path_prefix': path_prefix,
        'server_name': index,
        'build': '.',
        'container_name': f'{index}_container',
        'environment': environment
    }

    children = []
    for i in range(2):
        child_index = f"{index}_{i}" if index != "0" else f"{index}_{i}"
        child_node = generate_node(layer + 1, child_index, max_layers, path_prefix)
        if child_node:
            children.append(child_node)

    if children:
        node['children'] = children

    return node

def flatten_services(node, services):
    """
    Flatten the hierarchical structure into a dictionary of services.
    """
    service_name = node['server_name']
    services[service_name] = {
        'build': node['build'],
        'container_name': node['container_name'],
        'environment': node['environment']
    }
    if 'children' in node:
        for child in node['children']:
            flatten_services(child, services)

def create_docker_compose(layers):
    """
    Generate the hierarchical YAML structure and create docker-compose.yml.
    """
    root = generate_node(0, "0", layers)
    services = {}
    flatten_services(root, services)

    compose_content = {'version': '3.8', 'services': services}

    with open('docker-compose.yml', 'w') as file:
        yaml.dump(compose_content, file, default_flow_style=False)

if __name__ == "__main__":
    create_docker_compose(3)
