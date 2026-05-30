#!/usr/bin/python
import argparse
import time

from nlp_pipeline.tasks.directory_reader_bol_product_embedding import DirectoryReaderBolProductEmbedding

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A script to run a file through the DirectoryReaderBolProductEmbedding pipeline."
    )
    parser.add_argument("-b", "--bucket", default="dev-crawl-versed-ai", help="The bucket name", type=str)
    parser.add_argument(
        "-k",
        "--key",
        default="online-bolevidence-products/outputs/20240809/bc294b6d-0dbe-456b-b179-c364bfdefd97.tar.gz",
        help="The path to file in bucket",
        type=str,
    )

    parser.add_argument("-s", "--batch_size", default=5, help="The batch size", type=int)

    args = parser.parse_args()

    DirectoryReaderBolProductEmbedding().run(args.bucket, args.key, args.batch_size)

    time.sleep(600)
