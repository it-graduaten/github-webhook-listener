import json


def get_inputs_outputs_by_test_id(path_to_io_json, test_id):
    with open(path_to_io_json) as json_file:
        data = json.load(json_file)
        io_configs = data["ioConfig"]
        io_config = io_configs[test_id]
        inputs = io_config["inputs"]
        outputs = io_config["outputs"]
        return inputs, outputs
    return None, None
