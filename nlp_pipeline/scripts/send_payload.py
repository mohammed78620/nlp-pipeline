"""
Script for running NLP pipeline tasks using VertexAI.

Usage:
  python nlp_pipeline.py -e <endpoint> -f <file_path>

Arguments:
  -e, --endpoint   The endpoint for the NLP pipeline task. Available options: ner, re, nel, de, pe.
  -f, --file_path  Path to the file containing the JSON payload for the NLP task.

Example:
  python nlp_pipeline.py -e ner -f input.json

Example Payload for Date extraction endpoint:
{
    "instances": [
      {
        "id": "hkf3ha898231d",
        "text": "november 5th 2021"
      }
    ]
}


Note:
  Ensure that the JSON payload file contains valid input data for the specified NLP pipeline task.
"""

import argparse

import ujson

from nlp_pipeline.settings import (
    DE_ENDPOINT_NAME,
    NEL_ENDPOINT_NAME,
    NER_ENDPOINT_NAME,
    PE_ENDPOINT_NAME,
    RE_ENDPOINT_NAME,
)
from nlp_pipeline.utils.vertexai import VertexAI

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--endpoint", help="Endpoint Name", type=str)
    parser.add_argument("-f", "--file_path", help="File containing json payload", type=str)

    args = parser.parse_args()

    payload = ujson.load(open(args.file_path, "r"))
    endpoints = {
        "ner": NER_ENDPOINT_NAME,
        "re": RE_ENDPOINT_NAME,
        "nel": NEL_ENDPOINT_NAME,
        "de": DE_ENDPOINT_NAME,
        "pe": PE_ENDPOINT_NAME,
    }

    endpoint = endpoints.get(args.endpoint, None)

    if endpoint is None and args.endpoint:
        endpoint = args.endpoint

    vertexai = VertexAI(endpoint, True)

    success, result = vertexai.run(payload)

    print(result)
