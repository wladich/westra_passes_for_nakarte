from regions_tree import RegionsTree
import sys

[filename] = sys.argv[1:]

regions = RegionsTree.from_remote()
with open(filename, 'w') as f:
    regions.save_to_file(f)
