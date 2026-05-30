import argparse
import logging
import os
import re
import tarfile
import tempfile

from google.cloud import storage

from nlp_pipeline.settings import GOOGLE_PROJECT_ID
from nlp_pipeline.utils import htmlutils

logger = logging.getLogger()
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

_digits = re.compile(r"\d")


def contains_digits(input: str) -> bool:
    """
    Determine if string contains any numeral digits.

    Args:
        d (str): The thing to check

    Returns:
        bool: Whether or not digits were present.
    """
    return bool(_digits.search(input))


def process_file(file_path: str) -> None:
    """
    Determine if html file contains an invalid VID in the metadata.

    Invalid VIDs in this case would either start with some known ones
    that look suspicious (sussy) or lack any digits in them.

    Results appear in terminal.

    Args:
        file_path (str): Path to source file
    """
    looking_for = [
        "west-solutions-spa",
        "world-link-communications-inc-",
        "world-power-products",
        "yo-burrito",
        "yogofi-thesocialdataco-pte-ltd",
        "uk-safety-management-ltd",
        "vt-electronics",
        "dynamicforgefittings",
        "kunda-industrial-engineering-consultants",
        "worthington-assembly",
        "anping-shengfa-metal-products-co-ltd-",
        "r.j.-lipscomb-engineering-inc.",
    ]

    logger.debug(f"Processing {file_path}")

    with open(file_path, "r") as f:
        raw_content = f.read()
        content = htmlutils.process(raw_content)

        meta = content[0]
        vid = meta["extra_header_info"]["vid"]
        logger.debug(vid)

        for sussy in looking_for:
            if vid == sussy or vid.startswith(sussy):
                logger.warning(f"Found {vid} in {file_path}")

        if not contains_digits(vid):
            logger.warning(f"Sussy {vid} in {file_path}")


def process_archive(archive_path: str) -> None:
    """
    Process html files within archive to look for invalid VIDs

    Args:
        archive_path (str): raw Homepages crawl archive
    """
    with tempfile.TemporaryDirectory() as tmpdirname:
        logger.debug(f"Extracting {archive_path}")

        tar = tarfile.open(archive_path, "r:*")
        tar.extractall(tmpdirname)  # nosec
        tar.close()

        logger.debug(f"Extracted to {tmpdirname}")

        for root, _, files in os.walk(tmpdirname):
            for file_name in files:
                file_path = f"{root}/{file_name}"

                if file_path.endswith(".html") or file_path.endswith(".htm"):
                    process_file(file_path)


def process_blob(blob: str) -> None:
    """
    Download GS blob, process for invalid VIDs.

    Args:
        blob (str): GS blob representing a tar file
    """

    logger.info(f"Processing: {blob.name}")

    with tempfile.TemporaryDirectory() as tmpdirname:
        name = blob.name.split("/")[-1]
        download_loc = f"{tmpdirname}/{name}"
        blob.download_to_filename(download_loc)

        process_archive(download_loc)


def process_bucket(bucket: str, key: str) -> None:
    """
    Download tar file(s) in pointed to by key in bucket and process it to check
    for invalid VIDs

    Args:
        bucket (str): bucket name
        key (str): path to file or dir within bucket
    """
    storage_client = storage.Client(GOOGLE_PROJECT_ID)
    bucket = storage_client.get_bucket(bucket)
    blobs = bucket.list_blobs(prefix=key)
    for blob in blobs:
        if ".tar" in blob.name:
            process_blob(blob)
        else:
            logger.warning(f"None tar blob getting skipped: {blob.name}")


def args_process_bucket(args) -> None:
    """
    Simple wrapper for `process_bucket` that handles args from argparser
    """
    process_bucket(bucket=args.bucket, key=args.key)


def args_process_archive(args) -> None:
    """
    Simple wrapper for `process_archive` that handles args from argparser
    """
    process_archive(archive_path=args.filepath)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A script that can parse crawled Homepages archives to look for invalid looking VIDs."
    )

    subparsers = parser.add_subparsers(help="commands")

    # Process local file
    local_file_parser = subparsers.add_parser("local", help="Process a local archive file")
    local_file_parser.add_argument(
        "-f",
        "--filepath",
        help="Local file path",
        type=str,
    )
    local_file_parser.set_defaults(func=process_archive)

    # Process file from bucket
    bucket_parser = subparsers.add_parser("bucket", help="Process am archive file direct from GS bucket")
    bucket_parser.add_argument("-b", "--bucket", default="production-crawl-versed-ai", help="The bucket name", type=str)
    bucket_parser.add_argument(
        "-k",
        "--key",
        default="homepages/",
        help="The path to file or dir in bucket",
        type=str,
    )
    bucket_parser.set_defaults(func=process_bucket)

    args = parser.parse_args()
    if args.func.__name__ == "process_archive":
        args.func(args.filepath)
    else:
        args.func(args.bucket, args.key)
