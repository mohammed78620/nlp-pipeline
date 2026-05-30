#!/usr/bin/python
import argparse
import time

from nlp_pipeline.tasks.directory_reader import DirectoryReader
from nlp_pipeline.tasks.directory_reader_common_crawl import DirectoryReaderCommonCrawl
from nlp_pipeline.tasks.directory_reader_company_mentions import DirectoryReaderCompanyMentions
from nlp_pipeline.tasks.directory_reader_homepage import DirectoryReaderHomepage
from nlp_pipeline.tasks.directory_reader_lexis_nexis import DirectoryReaderLexisNexis

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--bucket", help="The Bucket name", type=str)
    parser.add_argument("-k", "--key", required=True, help="The key object")
    parser.add_argument("-s", "--batch_size", required=True, help="The batch size", type=int)
    parser.add_argument(
        "-r",
        "--reader",
        required=True,
        choices=["DR", "DRLN", "DRH", "DRCM", "DRCC"],
        help="The Directory reader to use",
    )

    args = parser.parse_args()
    directory_readers = {
        "DRLN": DirectoryReaderLexisNexis,
        "DR": DirectoryReader,
        "DRH": DirectoryReaderHomepage,
        "DRCM": DirectoryReaderCompanyMentions,
        "DRCC": DirectoryReaderCommonCrawl,
    }

    reader: DirectoryReader = directory_readers[args.reader]

    reader().run(args.bucket, args.key, args.batch_size)

    time.sleep(600)
