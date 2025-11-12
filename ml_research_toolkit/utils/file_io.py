import os
from pathlib import Path
import json
import yaml
import pickle
import pandas as pd
from typing import Any, Optional, Union, Dict

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
def save_json(obj: Any, filepath: Union[str, Path], indent: int = 4) -> None:
    """Save a Python object as JSON."""
    with open(filepath, "w") as f:
        json.dump(obj, f, indent=indent)


def load_json(filepath: Union[str, Path]) -> Any:
    """Load a JSON file."""
    with open(filepath, "r") as f:
        return json.load(f)


def save_yaml(obj: Any, filepath: Union[str, Path]) -> None:
    """Save a Python object as YAML."""
    with open(filepath, "w") as f:
        yaml.safe_dump(obj, f)


def load_yaml(filepath: Union[str, Path]) -> Any:
    """Load a YAML file."""
    with open(filepath, "r") as f:
        return yaml.safe_load(f)


def save_pickle(obj: Any, filepath: Union[str, Path]) -> None:
    """Save a Python object as a pickle."""
    with open(filepath, "wb") as f:
        pickle.dump(obj, f)


def load_pickle(filepath: Union[str, Path]) -> Any:
    """Load a pickle file."""
    with open(filepath, "rb") as f:
        return pickle.load(f)


def save_csv(df: pd.DataFrame, filepath: Union[str, Path], index: bool = False) -> None:
    """Save a DataFrame to CSV."""
    df.to_csv(filepath, index=index)


def load_csv(filepath: Union[str, Path]) -> pd.DataFrame:
    """Load a CSV file into a DataFrame."""
    return pd.read_csv(filepath)


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



# ----------------- Path Utilities -----------------
def resolve_path(path: Union[str, Path], must_exist: bool = False) -> Path:
    """
    Convert input to a Path object, optionally checking that it exists.

    Args:
        path (str | Path): Path to resolve.
        must_exist (bool): If True, raises error if path does not exist.

    Returns:
        Path: Resolved Path object.
    """
    p = Path(path).expanduser().resolve()
    if must_exist and not p.exists():
        raise FileNotFoundError(f"Path does not exist: {p}")
    return p
