from pathlib import Path

import yaml
import logging
import logging.config


with open(r'custom_logging/logging.yaml', 'r') as f:
    logging_configuration = yaml.safe_load(f.read())


def logging_setup(name: str, level: str = logging.DEBUG, log_file: str = 'app.log'):
    if not Path(f"log/").exists():
        Path(f"log/").mkdir(parents=True)

    log_file = f"log/{log_file}"

    logging_configuration['handlers']['file']['filename'] = log_file
    logging.config.dictConfig(logging_configuration)

    logger = logging.getLogger(name)

    return logger