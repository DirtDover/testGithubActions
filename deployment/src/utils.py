from typing import Dict

import yaml


def open_yaml(file: str) -> Dict:
    with open(file) as opened_file:
        content = yaml.load(opened_file, Loader=yaml.FullLoader)
    return content
