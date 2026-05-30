#!/usr/bin/python

import argparse

from nlp_pipeline.celery_app import app
from nlp_pipeline.tasks.directory_reader import DirectoryReader
from nlp_pipeline.tasks.directory_reader_bigtable_lexisnexis import DirectoryReaderBigtableLexisnexis
from nlp_pipeline.tasks.directory_reader_bigtable_webz import DirectoryReaderBigtableWebz
from nlp_pipeline.tasks.directory_reader_bol_evidence_descriptions import DirectoryReaderBolEvidenceDescriptions
from nlp_pipeline.tasks.directory_reader_bol_product_embedding import DirectoryReaderBolProductEmbedding
from nlp_pipeline.tasks.directory_reader_bol_product_extraction import DirectoryReaderBolProductExtraction
from nlp_pipeline.tasks.directory_reader_common_crawl import DirectoryReaderCommonCrawl
from nlp_pipeline.tasks.directory_reader_company_mentions import DirectoryReaderCompanyMentions
from nlp_pipeline.tasks.directory_reader_edgar import DirectoryReaderEdgar
from nlp_pipeline.tasks.directory_reader_homepage import DirectoryReaderHomepage
from nlp_pipeline.tasks.directory_reader_lexis_nexis import DirectoryReaderLexisNexis

if __name__ == "__main__":
    directory_readers = {
        "DR": DirectoryReader.name,
        "DRBED": DirectoryReaderBolEvidenceDescriptions().name,
        "DRBPEmbed": DirectoryReaderBolProductEmbedding().name,
        "DRBPExtract": DirectoryReaderBolProductExtraction().name,
        "DRCC": DirectoryReaderCommonCrawl().name,
        "DRCM": DirectoryReaderCompanyMentions().name,
        "DRE": DirectoryReaderEdgar().name,
        "DRH": DirectoryReaderHomepage.name,
        "DRLN": DirectoryReaderLexisNexis().name,
        "DRBigTableLexisnexis": DirectoryReaderBigtableLexisnexis().name,
        "DRBigTableWebz": DirectoryReaderBigtableWebz().name,
    }

    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--bucket", help="The Bucket name", type=str)
    parser.add_argument("-k", "--key", required=True, help="The key object")
    parser.add_argument("-s", "--batch_size", required=True, help="The batch size", type=int)
    parser.add_argument(
        "-r",
        "--reader",
        required=True,
        choices=list(directory_readers.keys()),
        help="The Directory reader to use",
    )

    args = parser.parse_args()

    name = directory_readers[args.reader]
    app.send_task(name, args=[args.bucket, args.key, args.batch_size], queue="directory-reader")
