#!/usr/bin/python
import argparse
import time

from nlp_pipeline.tasks.directory_reader_edgar import DirectoryReaderEdgar

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--bucket", default="dev-crawl-versed-ai", help="The bucket name", type=str)
    parser.add_argument(
        "-k",
        "--key",
        default="edgar/20240207/ABBV-1_0_1-1fc7b347-d313-4f2a-baca-fed86771f153.tar.bz2",
        help="The path to file",
        type=str,
    )
    parser.add_argument("-s", "--batch_size", default=5, help="The batch size", type=int)

    args = parser.parse_args()

    DirectoryReaderEdgar().run(args.bucket, args.key, args.batch_size)

    time.sleep(600)
