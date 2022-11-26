import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--master', action=argparse.BooleanOptionalAction)
args = parser.parse_args()
print(bool(args.master))
