import logging
import os
from configparser import ConfigParser

logger = logging.getLogger(__name__)


def get_config(local: bool = True) -> ConfigParser:
    """Reads config.ini and returns a configuration parser for it."""

    # later files in the list can be used to overwrite settings in the primary config file
    if local:
        config_files = ["config.ini", "config-local.ini"]
    else:
        config_files = ["config.ini"]
    if any([os.path.isfile(f) for f in config_files]):
        config = ConfigParser()
        config.read(config_files)
        return config

    raise ValueError(f"Config file(s) not found! Searched files: {config_files}")


def get_version() -> tuple:
    """Reads version.txt and returns its values in a tuple."""
    try:
        with open("version.txt") as file:
            split = file.read().splitlines()
            commit_hash = split[0]
            commit_date = split[1]

        return commit_hash, commit_date
    except Exception as e:
        logger.warning(f"Reading version.txt failed: {e}")
        return ()
