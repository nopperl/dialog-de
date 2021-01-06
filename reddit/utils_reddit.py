import json
from os import listdir
from os.path import join
import numpy as np


def get_turn_input_example():
    return {
        "ID": "",
        "turn_id": 0,
        "domains": [],
        "turn_domain": [],
        "turn_usr": "",
        "turn_sys": "",
        "turn_usr_delex": "",
        "turn_sys_delex": "",
        "belief_state_vec": [],
        "db_pointer": [],
        "dialog_history": [],
        "dialog_history_delex": [],
        "belief": {},
        "del_belief": {},
        "slot_gate": [],
        "slot_values": [],
        "slots": [],
        "sys_act": [],
        "usr_act": [],
        "intent": "",
        "turn_slot": [],
    }


def read_pairs(args, dial_files, max_line=None, min_words=1, max_words=128, ds_name=""):
    print(("Reading from {} for read_langs_turn".format(ds_name)))
    assert min_words >= 0
    assert min_words < max_words

    data = []

    for dial_file in dial_files:

        with open(dial_file, "r") as file:
            for line_number, line in enumerate(file):
                dialog_history = []
                dialog = json.loads(line)
                # Reading data
                turn_sys = ""
                for turn_number, turn in enumerate(dialog["turns"]):
                    text = turn["text"].strip()
                    # Check whether the text length is within the predefined range, otherwise end chain
                    if len(text.split()) not in range(min_words, max_words):
                        break
                    if turn["sender"] == "sys":
                        turn_sys = text
                    elif turn["sender"] == "user":
                        turn_user = text
                        data_detail = get_turn_input_example()
                        data_detail["ID"] = "{}-{}".format(ds_name, line_number)
                        data_detail["turn_id"] = turn_number % 2
                        data_detail["turn_usr"] = turn_user
                        data_detail["turn_sys"] = turn_sys
                        data_detail["dialog_history"] = list(dialog_history)

                        if not args["only_last_turn"]:
                            data.append(data_detail)

                        dialog_history.append(turn_sys)
                        dialog_history.append(turn_user)

                if args["only_last_turn"]:
                    data.append(data_detail)

                if max_line and line_number >= max_line:
                    break

    return data


def prepare_data_reddit(args):
    ds_name = "Reddit"
    if args["example_type"] != "turn":
        raise NotImplementedError
    max_line = args["max_line"]
    file_paths = [
        join(args["data_path"], "reddit", f)
        for f in listdir(join(args["data_path"], "reddit"))
        if f.endswith(".json")
    ]
    pairs = read_pairs(args, file_paths, max_line=max_line, ds_name=ds_name)
    random_idx = np.random.permutation(range(0, len(pairs)))
    train_idx = int(len(random_idx) * 0.8)
    dev_idx = int(len(random_idx) * 0.1)
    pairs_train = [p for i, p in enumerate(pairs) if i < train_idx]
    pairs_dev = [p for i, p in enumerate(pairs) if train_idx <= i < train_idx + dev_idx]
    pairs_test = [p for i, p in enumerate(pairs) if i >= train_idx + dev_idx]
    # TODO: dev and test set (probably not really needed)

    print("Read {} pairs train from {}".format(len(pairs_train), ds_name))
    print("Read {} pairs valid from {}".format(len(pairs_dev), ds_name))
    print("Read {} pairs test  from {}".format(len(pairs_test), ds_name))

    meta_data = {"num_labels": 0}

    return pairs_train, pairs_dev, pairs_test, meta_data
