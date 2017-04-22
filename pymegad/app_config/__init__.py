import logging
import os

import yaml

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')

LOGGER = logging.getLogger(__name__)

app_dir = os.path.dirname(__file__)
config_path = os.path.join(app_dir, 'config.yaml')

with open(config_path, 'r') as cfg:
    config = yaml.load(cfg)
    LOGGER.info('Config loaded: {}'.format(config))
