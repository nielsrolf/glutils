import json
import os
from collections import UserDict

import pandas as pd

def load_jsonl(jsonl_path):
    with open(jsonl_path, 'r') as f:
        return [json.loads(line) for line in f]


def write_jsonl(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')


def load_json(json_path):
    with open(json_path, 'r') as f:
        return json.load(f)


def write_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)


def load_csv(csv_path):
    return pd.read_csv(csv_path).to_dict(orient='records')


def load(path):
    print(f"Loading {path}")
    if path.endswith('.json'):
        return load_json(path)
    elif path.endswith('.jsonl'):
        return load_jsonl(path)
    elif path.endswith('.csv'):
        return load_csv(path)
    elif os.path.isdir(path):
        files = os.listdir(path)
        data = load(os.path.join(path, files[0]))
        if isinstance(data, list):
            for file in files[1:]:
                data += load(os.path.join(path, file))
            return data
        elif isinstance(data, dict):
            for file in files[1:]:
                data.update(load(os.path.join(path, file)))
            return data
    else:
        raise ValueError(f"Unknown file type: {path}")


def write(data, path):
    if path.endswith('.json'):
        return write_json(data, path)
    elif path.endswith('.jsonl'):
        return write_jsonl(data, path)
    else:
        raise ValueError(f"Unknown file type: {path}")
    

def dict_of_lists_to_list_of_dicts(dict_of_lists, category='category', value='value'):
    """Turns a dict like: {'a': [1, 2], 'b': [2, 3]} into [{category: 'a', value: 1}, {category: 'a', value: 2}, ...]"""
    result = []
    for key, values in dict_of_lists.items():
        for val in values:
            result.append({category: key, value: val})
    return result


class keydefaultdict(UserDict):
    def __init__(self, default_factory=None):
        super().__init__()
        self.default_factory = default_factory
    
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        value = self.default_factory(key)
        self[key] = value
        return value


def debug(f):
    def debugged(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            print(type(e), e)
            breakpoint()
            f(*args, **kwargs)
    return debugged


def dict_recursive(fn):
    """
    Decorator to apply a function to every leaf of a dict tree
    Arguments:
        fn: (d: Any, location: string) -> None, this should print something
    Returns:
        wrapped_fn
    """
    def wrapped_fn(d, location=""):
        if isinstance(d, dict):
            for k, v in d.items():
                wrapped_fn(v, f"{location}->{k}")
            return
        if isinstance(d, list):
            for k, v in enumerate(d):
                wrapped_fn(v, f"{location}->{k}")
            return
        fn(d, location)
    wrapped_fn.__name__ = fn.__name__
    return wrapped_fn
  
