# Copy of 'global utils' - a bunch will be irrelevant for this project
# https://github.com/nielsrolf/glutils/blob/main/glutils/__init__.py
import json
import os
from collections import UserDict

import pandas as pd
from glob import glob

import asyncio
from typing import Dict, Any, Coroutine

async def gather_dict(coros: Dict[Any, Coroutine]) -> Dict[Any, Any]:
    keys = list(coros.keys())
    results = await asyncio.gather(*coros.values())
    return dict(zip(keys, results))


def apply_to_files(f, glob_pattern, **kwargs):
    """Apply function f to all files matching glob_pattern
    Assumes f takes a `path` argument and any additional kwargs."""
    for path in glob(glob_pattern, recursive=True):
        f(path, *kwargs)


def load_jsonl(jsonl_path):
    with open(jsonl_path, 'r') as f:
        return [json.loads(line) for line in f]


def write_jsonl(data, path):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    except: pass
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
                try:
                    data += load(os.path.join(path, file))
                except:
                    print(f"Failed to load {file}")
            return data
        elif isinstance(data, dict):
            for file in files[1:]:
                try:
                    data.update(load(os.path.join(path, file)))
                except:
                    print(f"Failed to load {file}")
            return data
    else:
        raise ValueError(f"Unknown file type: {path}")


def write(data, path):
    if path.endswith('.json'):
        return write_json(data, path)
    elif path.endswith('.jsonl'):
        return write_jsonl(data, path)
    elif path.endswith('.csv'):
        return pd.DataFrame(data).to_csv(path, index=False)
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
  

def extract(text, tag):
    text = text.split(f'<{tag}>')[1].split(f'</{tag}>')[0].strip()
    try:
        return float(text)
    except:
        return text

def extract_tags(text, tags, prefix=''):
    values = {}
    for tag in tags:
        values[prefix + tag] = extract(text, tag)
    return values


import diskcache as dc
import hashlib


def recursive_access(d, keys):
    if d is None:
        return None
    if len(keys) == 1:
        return d[keys[0]]
    return recursive_access(d[keys[0]], keys[1:])


cache = None
# decorator for caching
def cache_on_disk(*cache_by_args):
    global cache
    if cache is None:
        cache = dc.Cache("cache")
    def decorator(func):
        import asyncio
        
        def get_cache_key(*args, **kwargs):
            if not cache_by_args:
                # If no specific args are provided, use all args and kwargs
                key_parts = list(args) + [f"{k}={v}" for k, v in kwargs.items()]
            else:
                key_parts = [recursive_access(kwargs, arg.split('.')) for arg in cache_by_args]
            
            key = "-".join([str(i) for i in key_parts])
            return hashlib.md5(key.encode()).hexdigest()

        if asyncio.iscoroutinefunction(func):
            async def wrapped(*args, **kwargs):
                key = get_cache_key(*args, **kwargs)
                
                if key in cache:
                    return cache[key]
                result = await func(*args, **kwargs)
                cache[key] = result
                return result
        else:
            def wrapped(*args, **kwargs):
                key = get_cache_key(*args, **kwargs)
                
                if key in cache:
                    return cache[key]
                result = func(*args, **kwargs)
                cache[key] = result
                return result
        
        wrapped.__name__ = func.__name__
        return wrapped
    
    return decorator