import os
import re
import tarfile
import tempfile
from typing import Any, Dict, List, Tuple, Union

import ujson
from celery import Celery


def remove_files(file_paths: List[str]) -> None:
    """
    remove all files specified in list of file_paths

    Args:
        file_paths (List[str]): list of file paths
    """
    for file_path in file_paths:
        if os.path.isfile(file_path):
            os.remove(file_path)


def create_compressed_file(data: Any, file_name: str, location: str, as_jsonl: bool = False) -> Tuple[str, str]:
    """
    Creates an archive containing `data` saved as a JSON file or JSONL.

    Args:
        data (Any): The data to be saved to file.
        file_name (str): The name of the archive (without extension).
        location (str): Where to create the archive.
        as_jsonl (bool): Whether or not to save in JSONL format. If False, JSON.

    Returns:
        Tuple[str, str]: Full path to archive and the file name.
    """
    compressed_file_name = f"{file_name}.tar.gz"
    compressed_file_path = f"{location}/{compressed_file_name}"

    # The umcompressed file should be temporary
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_name_with_ext = f"{file_name}.json"
        if as_jsonl:
            file_name_with_ext = f"{file_name}.jsonl"

        file_path = f"{tmp_dir}/{file_name_with_ext}"

        with open(file_path, "w+") as f:
            if as_jsonl:
                for row in data:
                    serialised = ujson.dumps(row)
                    f.write(f"{serialised}\n")
            else:
                ujson.dump(data, f, ensure_ascii=False, indent=4)

        # Compress temporary file
        with tarfile.open(compressed_file_path, "w:gz") as tar:
            tar.add(file_path, arcname=f"{file_name_with_ext}")

    return compressed_file_path, compressed_file_name


def publish_to_queue(app: Celery, message: Union[List, Dict], queue_name: str) -> None:
    """
    Publishes a message to a specified queue using Celery.

    Args:
        app (Celery): The Celery application instance.
        message (Union[List, Dict]): The message to be published to the queue. It can be either a list or a dictionary.
        queue_name (str): The name of the queue to publish the message to.

    Returns:
        None: This function does not return anything.
    """
    with app.connection() as connection:
        producer = connection.Producer(serializer="json")
        producer.publish(body=message, exchange="", routing_key=queue_name)


def remove_urls(text: str, replacement_text: str = ""):
    """
    remove all urls from text

    Args:
        text (str): text to remove urls from
        replacement_text (str, optional): the text to replace urls. Defaults to "".

    Returns:
        _type_: text without urls
    """
    url_pattern = re.compile(r"https?://\S+|www\.\S+")
    urls = url_pattern.findall(text)

    for url in urls:
        text = text.replace(url, replacement_text)

    return text.strip()
