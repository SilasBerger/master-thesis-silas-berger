import json
import os

from src.util.ConfigNotLoadedError import ConfigNotLoadedError
from src.util.CredentialsNotLoadedError import CredentialsNotLoadedError
from src.util import paths


_config = None
_credentials = None


def load_config(config_file_name="config_default.json", custom_path=False):
    """
    Load specified configuration file into context, use config_default of no file specified
    :param config_file_name: name or path of config file, if using other than config_default
    :param custom_path: if True, `config_file_name` is interpreted as a path, rather than the
           name of a file in the /configs directory
    """
    global _config
    if custom_path:
        file_path = paths.convert_project_relative_path(config_file_name)
    else:
        file_path = os.path.join(get_configs_dir(), config_file_name)
    with open(file_path, "r") as f:
        _config = json.load(f)


def load_credentials(credentials_file_name="credentials_default.json", custom_path=False):
    """
    Load specified credentials file into context, use credentials_default of no file specified
    :param credentials_file_name: name or path of credentials file, if using other than credentials_default
    :param custom_path: if True, `credentials_file_name` is interpreted as a path, rather than the
           name of a file in the /configs directory
    """
    global _credentials
    if custom_path:
        file_path = paths.convert_project_relative_path(credentials_file_name)
    else:
        file_path = os.path.join(get_configs_dir(), credentials_file_name)
    with open(file_path, "r") as f:
        _credentials = json.load(f)


def get_config(key):
    """
    Get config item by key. Throws exception if key doesn't exist.
    :param key: key of the desired config item
    :return: config item with specified key
    """
    if _config is None:
        raise ConfigNotLoadedError()
    return _config[key]


def get_credentials(key):
    """
    Get credentials item by key. Throws exception if key doesn't exist.
    :param key: key of the desired credentials item
    :return: credentials item with specified key
    """
    if _credentials is None:
        raise CredentialsNotLoadedError()
    return _credentials[key]


def get_configs_dir():
    """
    Get path to default configs directory
    :return: path to configs directory
    """
    return os.path.join(paths.get_project_root(), "configs")
