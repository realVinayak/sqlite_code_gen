from sqlite_code_gen import perform_parse
import argparse
import os

parser = argparse.ArgumentParser()

parser.add_argument("-i", "--input", help="Input SQL file to parse", type=str, required=True)
parser.add_argument("-o", "--output", help="Output C file", type=str, required=True)
parser.add_argument("-f", "--format", help="Set to format C file (requires clang-format)", action="store_true")


def main():
    args = parser.parse_args()
    with open(args.input) as f:
        lines = f.readlines()
    
    file = perform_parse(lines)
    file_str = '\n'.join(file)
    
    with open(args.output, "w") as f:
        f.write(file_str)
    
    if args.format:
        os.system(f"clang-format -i {args.output}")

if __name__ == '__main__':
    main()
    