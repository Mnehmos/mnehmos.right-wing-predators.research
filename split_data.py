#!/usr/bin/env python3
"""
Script to split data.json into multiple smaller JSON files
Each file will contain up to 100 entries for better performance
"""

import json
import os
import math

def split_json_data(input_file='data.json', output_dir='data', entries_per_file=100):
    """
    Split a large JSON file into smaller chunks

    Args:
        input_file: Path to the input JSON file
        output_dir: Directory to store the split files
        entries_per_file: Number of entries per output file
    """

    # Read the original JSON file
    print(f"Reading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_entries = len(data)
    num_files = math.ceil(total_entries / entries_per_file)

    print(f"Total entries: {total_entries}")
    print(f"Entries per file: {entries_per_file}")
    print(f"Number of files to create: {num_files}")

    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}/")

    # Split the data into chunks
    for i in range(num_files):
        start_idx = i * entries_per_file
        end_idx = min((i + 1) * entries_per_file, total_entries)
        chunk = data[start_idx:end_idx]

        output_file = os.path.join(output_dir, f'data-{i + 1}.json')

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunk, f, indent=2, ensure_ascii=False)

        print(f"Created {output_file} with {len(chunk)} entries (IDs {chunk[0]['id']}-{chunk[-1]['id']})")

    # Create an index file listing all the data files
    index_data = {
        "total_entries": total_entries,
        "entries_per_file": entries_per_file,
        "num_files": num_files,
        "files": [f"data/data-{i + 1}.json" for i in range(num_files)]
    }

    index_file = os.path.join(output_dir, 'index.json')
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2)

    print(f"\nCreated index file: {index_file}")
    print(f"\n✓ Successfully split {total_entries} entries into {num_files} files!")
    print(f"✓ Each file contains up to {entries_per_file} entries")

if __name__ == '__main__':
    split_json_data()
