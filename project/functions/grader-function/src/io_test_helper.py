import json
import os


def get_io_config(path_to_io_json):
    if path_to_io_json is None:
        return None

    if not os.path.exists(path_to_io_json):
        return None

    with open(path_to_io_json) as json_file:
        data = json.load(json_file)
        io_configs = data["ioConfig"]
        return io_configs
