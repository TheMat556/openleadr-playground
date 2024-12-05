import yaml


def create_docker_compose(num_containers):
  services = {}
  for i in range(1, num_containers + 1):
    service_name = f'tst{i}'
    services[service_name] = {
      'build': '.',
      'container_name': f'{service_name}_container',
      'environment': [f'NAME={service_name}'],
    }

  compose_content = {'version': '3.8', 'services': services}

  with open('docker-compose.yml', 'w') as file:
    yaml.dump(compose_content, file, default_flow_style=False)


# Example usage: create a docker-compose file with 2 containers
create_docker_compose(2)
