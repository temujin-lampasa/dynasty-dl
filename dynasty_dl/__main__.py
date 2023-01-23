import os
import argparse
from pathlib import Path
from . import Dynasty

def main() -> None:
    parser = argparse.ArgumentParser(description="Download series or chapters from dynasty-scans.")
    parser.add_argument("url", help="chapter or series url")
    parser.add_argument("--dir", help="download directory", metavar='dir')
    args = parser.parse_args()
    
    dynasty = Dynasty()
    if "/chapters/" in args.url:
        if args.dir:
            download_dir = args.dir
        else:
            download_dir = os.path.join('.', args.url.rstrip('/').split('/')[-1])
        dynasty.download_chapter(args.url, download_dir)
    elif "/series/" in args.url:
        if args.dir:
            download_dir = args.dir
        else:
            download_dir = '.'
        dynasty.download_series(args.url, download_dir)


if __name__ == "__main__":
    main()
