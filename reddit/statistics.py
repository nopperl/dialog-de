#!/usr/bin/env python3
from argparse import ArgumentParser
from itertools import chain
from json import loads
from os import listdir
from os.path import join, splitext, basename
from typing import List, Dict
import numpy as np


def retrieve_statistics(data_path):
    dialog_files = [
        join(data_path, f) for f in listdir(data_path) if f.endswith(".json")
    ]
    num_dialogs_per_sub: Dict[str, int] = {}
    turns_per_sub: Dict[str, List[int]] = {}
    lengths_per_sub: Dict[str, List[int]] = {}
    words_per_sub: Dict[str, List[int]] = {}
    for dialog_file in dialog_files:
        with open(dialog_file, "r") as file:
            sub = splitext(basename(dialog_file))[0]
            turns = []
            lengths = []
            words = []
            num_dialogs = 0
            for line in file:
                num_dialogs += 1
                dialog = loads(line)
                turns.append(len(dialog["turns"]))
                lengths.extend([len(turn["text"]) for turn in dialog["turns"]])
                words.extend([len(turn["text"].split()) for turn in dialog["turns"]])
            turns_per_sub[sub] = turns
            lengths_per_sub[sub] = lengths
            words_per_sub[sub] = words
            num_dialogs_per_sub[sub] = num_dialogs
    total_dialogs = sum(num_dialogs_per_sub.values())
    return num_dialogs_per_sub, turns_per_sub, lengths_per_sub, words_per_sub


def print_statistics(values_per_sub: Dict[str, List[int]], prefix: str):
    values = list(chain(*values_per_sub.values()))
    print(
        f"{prefix}: min={min(values)}, mean={np.mean(values)}, stdev={np.std(values)}, max={max(values)}"
    )


def main():
    parser = ArgumentParser()
    parser.add_argument("-d", "--data", default="data/reddit")
    args = parser.parse_args()
    data_path = args.data
    result = retrieve_statistics(data_path)
    total_dialogs = sum(result[0].values())
    print(f"Number of dialogues: {total_dialogs}")
    print_statistics(result[1], "Turns per dialogue")
    print_statistics(result[2], "Turn lengths")
    print_statistics(result[3], "Words per turn")


if __name__ == "__main__":
    main()
