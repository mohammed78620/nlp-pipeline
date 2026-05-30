import argparse
import difflib
import os

from nlp_pipeline.utils.process_input_function import prepare_text


def load_hashes(hash_list_file):
    lines = {}

    with open(hash_list_file, "r") as f:
        f.readline()  # ignore header

        for line in f:
            filename, hash = line.split(",", 1)
            hash = hash.split("\n")[0]

            if hash in lines.keys():
                lines[hash].append(filename)
            else:
                lines[hash] = [filename]
    return lines


def filter_non_dupes(hash_list):
    delete_keys = [key for key in hash_list.keys() if len(hash_list[key]) < 2]
    for key in delete_keys:
        del hash_list[key]


def load_source_file(source_dir, filename, skip_first: int = 1):
    file_path = os.path.join(source_dir, filename)

    with open(file_path, "r") as f:
        lines = f.readlines()[skip_first:]

        text = " ".join(lines)
        prepared = prepare_text(text)

        lines = prepared["cleaned_text"].split("\n")
        lines = [line + "\n" for line in lines if line.strip() != ""]
    return lines


def main(hash_list, source_data, output_file):
    hashes = load_hashes(hash_list)
    print(len(hashes.keys()))

    filter_non_dupes(hashes)
    print(len(hashes.keys()))

    with open(output_file, "w") as f:
        for hash, files in hashes.items():
            original = load_source_file(source_data, files[0])

            for file in files[1:]:
                comparator = load_source_file(source_data, file)

                f.write(f"Comparing: {files[0]} -> {file}\n")
                f.write(f"Hash: {hash}\n")

                if comparator == original:
                    f.write("Same content\n")
                else:
                    diff = difflib.context_diff(original, comparator)
                    for i in diff:
                        f.write(i)

                f.write("\n\n\n===================\n\n\n\n\n\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser("Produce the diff for files found by lsh-test.py to have hash collisions.")
    p.add_argument("--hash_list", type=str, help="CSV file of filename and its hash")
    p.add_argument("--source_data", type=str, help="Dir of source files")
    p.add_argument("--output_file", type=str, help="Output file")

    args = p.parse_args()

    main(args.hash_list, args.source_data, args.output_file)
