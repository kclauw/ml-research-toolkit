import os
from pathlib import Path
import json
import yaml
import pickle
import pandas as pd
from typing import Any, Optional, Union, Dict
import hashlib
import dill
import csv
import itertools

# ----------------- Folder Utilities -----------------
def create_folder(path: Union[str, Path], exist_ok: bool = True) -> Path:
    """
    Create a folder if it does not exist.

    Args:
        path (str | Path): Folder path to create.
        exist_ok (bool, optional): If True, do not raise an error if folder exists. Defaults to True.

    Returns:
        Path: Path object of the created folder.
    """
    folder = Path(path)
    folder.mkdir(parents=True, exist_ok=exist_ok)
    return folder

# ----------------- File Utilities -----------------
def save_json(obj: Any, folder: Union[str, Path], filename: str, indent: int = 4) -> None:
    filepath = resolve_path(folder, filename)
    with open(filepath, "w") as f:
        json.dump(obj, f, indent=indent)


def load_json(folder_or_filepath: Union[str, Path], filename: str = None) -> Any:
    filepath = resolve_path(folder_or_filepath, filename)
    with open(filepath, "r") as f:
        return json.load(f)


def save_yaml(obj: Any, folder: Union[str, Path], filename: str) -> None:
    filepath = resolve_path(folder, filename + ".yaml")
    with open(filepath, "w") as f:
        yaml.safe_dump(obj, f)


def load_yaml(folder_or_filepath: Union[str, Path], filename: str = None) -> Any:
    filepath = resolve_path(folder_or_filepath, filename)
    with open(filepath, "r") as f:
        return yaml.safe_load(f)

def save_pickle(obj: Any, folder: Union[str, Path], filename: str) -> None:
    filepath = resolve_path(folder, filename)
    with open(filepath, "wb") as f:
        pickle.dump(obj, f)


def load_pickle(folder_or_filepath: Union[str, Path], filename: str = None) -> Any:
    filepath = resolve_path(folder_or_filepath, filename)
    with open(filepath, "rb") as f:
        return pickle.load(f)

def save_csv(df: pd.DataFrame, folder: Union[str, Path], filename: str, index: bool = False) -> None:
    filepath = resolve_path(folder, filename)
    df.to_csv(filepath, index=index)

def load_csv(folder : str, filename: str) -> pd.DataFrame:
    return pd.read_csv(os.path.join(folder, filename))

def load_dill(folder : str, filename: str):
    with open(os.path.join(folder, filename), 'rb') as f:
        return dill.load(f)
    
def save_dataframe(df: Any, folder: Union[str, Path], filename: str) -> None:
    create_folder(folder)
    filepath = os.path.join(folder, filename)
    df.to_csv(filepath, index=False)

def load_dataframe(folder: Union[str, Path], filename: str = None) -> Any:
    filepath = os.path.join(folder, filename + ".csv")
    return pd.read_csv(filepath)
    
def load_job_hparams(job_folder, job_id):
    filename = os.path.join(job_folder, 'job_%d.csv' % (job_id))
    rows = []
    with open(filename, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)  # Reads CSV as a dictionary
        for row in reader:
            rows.append(row)
    return rows

def gridsearch_params(search_params):
    """
    Generate all combinations of parameters from cfg['params'] as a list of dictionaries.
    Excludes 'track' from the grid search but keeps it in the final dict if present.

    Args:
        cfg (dict): Configuration dictionary with a "params" key.

    Returns:
        List[Dict[str, Any]]: List of all parameter combinations.
    """
    # Copy params and remove 'track' from the search space
    #search_params = {k: v for k, v in cfg.items()}

    # Ensure all values are lists
    search_params = {k: v if isinstance(v, list) else [v] for k, v in search_params.items()}

    keys = list(search_params.keys())
    values = list(search_params.values())

    param_list = []
    for combo in itertools.product(*values):
        params = dict(zip(keys, combo))
        param_list.append(params)

    return param_list

# ----------------- Dictionary Utilities -----------------
from typing import Dict, List, Any, Optional


def select_keys_from_dict(data: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
    """
    Return a new dictionary containing only the specified keys.

    Args:
        data (dict): Input dictionary.
        keys (list[str]): Keys to keep.

    Returns:
        dict: Dictionary containing only the selected keys.
    """
    if not isinstance(data, dict):
        try:
            data = dict(data)
        except Exception:
            raise ValueError(f"Cannot convert input of type {type(data)} to dict.")

    return {k: data[k] for k in keys if k in data}


def remove_keys_from_dict(data: Dict[str, Any], keys: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Return a new dictionary with the specified keys removed.

    Args:
        data (dict): Input dictionary.
        keys (list[str], optional): Keys to remove. Defaults to None.

    Returns:
        dict: Dictionary with specified keys removed.
    """
    if not isinstance(data, dict):
        try:
            data = dict(data)
        except Exception:
            raise ValueError(f"Cannot convert input of type {type(data)} to dict.")

    keys_to_remove = set(keys or [])
    return {k: v for k, v in data.items() if k not in keys_to_remove}

def dict_to_filename(
            data: Dict[str, Any],
            delimiter: str = "_",
            ignore_keys: Optional[List[str]] = None,
            select_keys: Optional[List[str]] = None,
        ) -> str:
            """
            Combine dictionary keys and values into a string with a delimiter.

            Args:
                data (dict): Input dictionary.
                delimiter (str, optional): Delimiter between key-value pairs. Defaults to "_".
                ignore_keys (list[str], optional): Keys to ignore. Defaults to None.
                select_keys (list[str], optional): If provided, only use these keys. Defaults to None.

            Returns:
                str: Combined string of keys and values.
            """
            if not isinstance(data, dict):
                try:
                    data = dict(data)
                except Exception:
                    raise ValueError(f"Cannot convert input of type {type(data)} to dict.")

            # Filter dictionary based on ignore_keys or select_keys
            if select_keys:
                filtered_data = select_keys_from_dict(data, select_keys)
            elif ignore_keys:
                filtered_data = remove_keys_from_dict(data, ignore_keys)
            else:
                filtered_data = data

            # Combine keys and values
            return delimiter.join(f"{k}{delimiter}{v}" for k, v in sorted(filtered_data.items()))

def dict_to_hash(params):
    return hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()[:8]



# ----------------- Path Utilities -----------------
def resolve_path(folder: Union[str, Path, None], filename: Union[str, None]) -> Path:
    """Return a resolved Path from folder+filename or a single filepath."""
    if folder is not None and filename is not None:
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        return folder / filename

    if folder is not None and filename is None:
        return Path(folder)

    raise ValueError("Either provide (folder + filename) for saving, or folder=filepath for loading.")

def seed_all(seed: int, seed_python=True, seed_numpy=True, seed_torch=True, seed_jax=True):
    """
    Set seeds for reproducibility across multiple libraries.

    Args:
        seed (int): The seed value.
        seed_python (bool): Whether to seed Python's `random`.
        seed_numpy (bool): Whether to seed `numpy`.
        seed_torch (bool): Whether to seed PyTorch.
        seed_jax (bool): Whether to seed JAX.
    """
    print(f"[INFO] Seeding everything with seed={seed}")

    if seed_python:
        import random
        random.seed(seed)
        os.environ["PYTHONHASHSEED"] = str(seed)

    if seed_numpy:
        import numpy as np
        np.random.seed(seed)

    if seed_torch:
        try:
            import torch
            torch.manual_seed(seed)
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
        except ImportError:
            print("[WARNING] PyTorch not installed, skipping torch seeding.")

    if seed_jax:
        try:
            import jax
            global _jax_key
            _jax_key = jax.random.PRNGKey(seed)
        except ImportError:
            print("[WARNING] JAX not installed, skipping JAX seeding.")

    return seed

def matches_params(config, params):
    for key, value in params.items():
        print((key, value, config[key]))
        if key not in config:
            return False
        if config[key] != value:
            return False
    return True

def find_runs_by_params(root_dir: str, params: Dict) -> List[str]:
    """
    Retrieve all run folders under `root_dir` grouped by datetime folders.
    Each datetime folder may contain multiple runs with config.yaml files.

    Args:
        root_dir (str): Root directory containing datetime folders.
        params (dict): Key-values that must match in each run's config.yaml.

    Returns:
        List[str]: Sorted list of full paths to matching run folders.
    """

    matching_runs, matching_cfgs = [], []

    # Loop over datetime folders at top level
    for datetime_folder in sorted(os.listdir(root_dir)):
        dt_path = os.path.join(root_dir, datetime_folder)
        print(datetime_folder)
        if not os.path.isdir(dt_path):
            continue

        # Now walk through runs inside each datetime folder
        for dirpath, dirnames, filenames in os.walk(dt_path):
            if 'config.yaml' not in filenames:
                continue

            config_path = os.path.join(dirpath, 'config.yaml')
            

            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)

                
                if matches_params(config, params):
                    matching_runs.append(dirpath)
                    matching_cfgs.append(config)

            except Exception as e:
                print(f"[WARNING] Failed to read {config_path}: {e}")

    # Sort final matches by datetime + folder name
    #matching_runs.sort(key=lambda p: p)

    return matching_runs, matching_cfgs