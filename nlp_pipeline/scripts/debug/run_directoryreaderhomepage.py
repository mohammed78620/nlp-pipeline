#!/usr/bin/python
import argparse
import time

from nlp_pipeline.tasks.directory_reader_homepage import DirectoryReaderHomepage

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--bucket", default="dev-crawl-versed-ai", help="The bucket name", type=str)
    parser.add_argument(
        "-k",
        "--key",
        default="homepages/homepages_20230516_b80c93b05fb25bf4a304f5de00e50795.tar.tar",
        help="The path to file",
        type=str,
    )
    parser.add_argument("-s", "--batch_size", default=5, help="The batch size", type=int)

    args = parser.parse_args()

    DirectoryReaderHomepage().run(args.bucket, args.key, args.batch_size)

    time.sleep(600)
