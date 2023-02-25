from regions_tree import RegionsTree
import sys
from argparse import ArgumentParser

def main():
    parser = ArgumentParser()
    parser.add_argument('output_tree')
    parser.add_argument('--api-host', default='https://westra.ru')
    parser.add_argument('--api-key', required=True)
    conf = parser.parse_args()

    regions = RegionsTree.from_remote(conf.api_key)
    with open(conf.output_tree, 'w') as f:
        regions.save_to_file(f)


if __name__ == '__main__':
    main()


