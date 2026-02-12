#!/usr/bin/python3
"""
Usage: multifit config

    -h --help           Print this help screen and exit.
"""
from importlib import resources

from docopt import docopt

def main():
    """Generate a config file"""
    args = docopt(__doc__)

    container = resources.files('multifit')
    empty_config = container.joinpath('templates', 'empty_input_file.yml').read_text()
    print(empty_config)


if __name__ == '__main__':
    main()
