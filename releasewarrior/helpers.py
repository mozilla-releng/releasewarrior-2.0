import logging
import os
import sys
import json

import yaml

DEFAULT_CONFIG = os.path.join(
    os.path.abspath(os.path.join(os.path.realpath(__file__), '..', '..')),
    "releasewarrior/configs/config.yaml"
)

DEFAULT_TEMPLATES_DIR = os.path.join(
    os.path.abspath(os.path.join(os.path.realpath(__file__), '..', '..')),
    "releasewarrior/templates"
)


def get_logger(verbose=False):
    log_level = logging.INFO
    if verbose:
        log_level = logging.DEBUG

    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s",
                        stream=sys.stdout,
                        level=log_level)
    logger = logging.getLogger("releasewarrior")
    logger.setLevel(logging.DEBUG)

    return logger


def get_config(path=DEFAULT_CONFIG):
    with open(path) as fh:
        config = yaml.load(fh)
    config['templates_dir'] = config.get('templates_dir', DEFAULT_TEMPLATES_DIR)
    return config


def load_json(path):
    data = {}
    with open(path) as f:
        data.update(json.load(f))
    return data

