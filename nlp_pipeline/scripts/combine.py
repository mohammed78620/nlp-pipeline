#!/usr/bin/python

import argparse
import json
import logging
import os
import tarfile
import tempfile

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, help="The AWS S3 Bucket name", type=str)
    parser.add_argument("-o", "--output", required=True, help="The AWS S3 key object")

    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as tmpdirname:
        for _, _, files in os.walk(args.input):
            for file_name in files:
                file_path = f"{args.input}/{file_name}"
                try:
                    tar = tarfile.open(file_path, "r:*")
                except tarfile.ReadError as e:
                    logger.error("Couldn't figure out how to uncompress archive.")
                    raise e

                tar.extractall(tmpdirname)  # nosec
                tar.close()

        result = dict()
        for _, _, files in os.walk(tmpdirname):
            for file in files:
                file_path = f"{tmpdirname}/{file}"
                if file.endswith("json"):
                    with open(file_path, "r") as infile:
                        result.extend(json.load(infile))
