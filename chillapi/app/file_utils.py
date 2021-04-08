import yaml


def read_yaml(file):
    with open(file) as file:
        yaml_file = yaml.load(file, Loader=yaml.FullLoader)
    return yaml_file
