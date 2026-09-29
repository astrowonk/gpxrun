import argparse

from . import GpxRun


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="gpx file to process")
    args = parser.parse_args()
    g = GpxRun(args.file)


if __name__ == "__main__":
    main()
