import os
import sys

from src.util import context


def convert_project_relative_path(rel_path):
    """
    Converts a relative path within the project to an absolute path.
    :param rel_path: relative path to be converted, must at or below project root
    :return: absolute path to specified location
    """
    return os.path.normpath(os.path.join(get_project_root(), rel_path))


def get_project_root():
    """
    Returns path to project root
    :return: path to project root
    """
    parent, src_folder = os.path.split(os.path.dirname(sys.modules['__main__'].__file__))
    base_path = os.path.normpath(parent)
    return base_path