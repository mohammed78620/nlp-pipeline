"""
Description: This script purpouse is to debug Local Sensitive Hashing with crawled html articles. It takes as input a direectory of articles and
processes each thorugh lsh fingerprinting. As a result, it creates a csv file where each row contains two columns, the article file name and the resulting
fingerprint.
Usage: poetry run python -m nlp_pipeline.scripts.debug.lsh-test -i <articles-directory>
"""

import argparse
import csv
import logging
import os

from nlp_pipeline.utils.fingerprint import LSHFingerprintStore
from nlp_pipeline.utils.process_input_function import process_crawled_html

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, help="The source folder to process", type=str)
    parser.add_argument("-s", "--seed", required=False, default=1, help="LSH Seed", type=int)
    parser.add_argument("-mj", "--min_jaccard", required=False, default=0.5, help="LSH Jaccard value", type=float)
    parser.add_argument("-o", "--output", required=False, default="result", help="The output file name", type=str)
    parser.add_argument("-v", "--verbose", action="store_true", help="Run in verbose mode")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    logger = logging.getLogger("lsh-test")

    # Create a new lsh store with the given seed and jaccard values
    store = LSHFingerprintStore(args.seed, args.min_jaccard)
    logger.info(f"LSH Fingerprint Store initialised with seed={args.seed} and jaccard={args.min_jaccard}")

    # Create a new csv file
    csvfile = open(f"{args.output}.csv", "w+")
    fieldnames = ["file_name", "fingerprint"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # Process each article in the directory
    for file_name in os.listdir(args.input):
        file_path = os.path.join(args.input, file_name)
        raw_html = open(file_path, encoding="utf-8", errors="ignore").read().strip()
        text = process_crawled_html(raw_html)

        if text:
            hash = store.get_fingerprint(text["text"])

            logger.debug(f"File {file_name} yields hash: {hash}")
            writer.writerow({"file_name": file_name, "fingerprint": hash})
