#!/usr/bin/env python
"""
Write a docker-compose configuration for multiple clients.

This script uses the docker-compose-dev.yaml.j2 template to generate a
docker-compose configuration for multiple clients. The number of clients is
specified by the first argument. The generated configuration is written to
'../docker-compose-dev.yaml'.
"""
from pathlib import Path
from os import getenv
from jinja2 import Environment, FileSystemLoader


def load_yaml_template(template_file: Path, params: dict) -> str:
    env = Environment(loader=FileSystemLoader('/'))
    template = env.get_template(str(template_file))
    return template.render(**params)


def main(argv):
    if len(argv) != 2:
        print('Usage: compose_multiple_clients.py <number of clients>')
        return 1
    
    try:
        num_clients = int(argv[1])
    except ValueError:
        print('The number of clients must be an integer')
        return 1
    
    root_dir = Path(__file__).parent.parent
    template_file = root_dir / 'scripts/docker-compose-dev.yaml.j2'
    compose_file =  root_dir / 'docker-compose-dev.yaml'

    yaml_config = load_yaml_template(template_file, {'num_clients': num_clients})
    compose_file.write_text(yaml_config)

if __name__ == '__main__':
    from sys import argv
    main(argv)
