import os
import csv
from typing import Any, List

#import pandas as pd

import polars as pl

class CSVLogger:
    def __init__(self, folder: str, filename: str, autosave: bool = True):
        """
        Logger that appends rows to a CSV file efficiently.

        Args:
            folder (str): Directory to save the log file.
            filename (str): Name of the log file (without extension).
            autosave (bool): Whether to save after every log append.
        """

            
        self.filepath = os.path.join(folder, filename + ".csv")
      
        self.autosave = autosave
        self.headers_written = os.path.exists(self.filepath)

        os.makedirs(folder, exist_ok=True)

        # Track order of keys for consistency
        self.keys = None

    def log(self, **kwargs: Any):
        """
        Append one row to the CSV.
        Example:
            logger.log(loss=0.1, reward=5)
        """
        if self.keys is None:
            self.keys = list(kwargs.keys())

        # Enforce consistent column order
        row = []
        for k in self.keys:
            v = kwargs.get(k, None)
            # Convert NumPy arrays to lists
            if hasattr(v, "tolist"):
                v = v.tolist()
            # Convert lists to string with brackets
            if isinstance(v, list):
                v = str(v)  # keeps brackets, adds commas automatically
            row.append(v)

        if self.autosave:
            self._append_row(row)

    def _append_row(self, row: List[Any]):
        """Append a single row to the CSV, writing header if needed."""
        new_file = not os.path.exists(self.filepath)

        with open(self.filepath, "a", newline="") as f:
            writer = csv.writer(f)
            if new_file or not self.headers_written:
                writer.writerow(self.keys)
                self.headers_written = True
            writer.writerow(row)
            f.flush()
            os.fsync(f.fileno())  # Force write to disk

    def to_dataframe(self) -> pl.DataFrame:
        """Return logs as a Polars DataFrame."""
        if not os.path.exists(self.filepath):
            return pl.DataFrame()
        try:
            return pl.read_csv(self.filepath)
        except Exception as e:
            raise RuntimeError(f"Failed to load DataFrame from {self.filepath}: {e}")

    def get(self, key: str) -> List[Any]:
        """Get all logged values for a key."""
        df = self.to_dataframe()
        return df[key].tolist() if key in df else []


    def load_from_disk(self):
        """
        Load an existing CSV log into a CSVLogger instance.

        Args:
            folder (str): Directory where the CSV file is stored.
            filename (str): Name of the CSV file (without extension).
            autosave (bool): Whether to save after every log append.

        Returns:
            CSVLogger: Logger instance with keys populated from file.
        """
        if os.path.exists(self.filepath):
            df = pl.read_csv(self.filepath)
            if not df.is_empty():
                self.keys = list(df.columns)
                self.headers_written = True
        return df
    
    def remove(self):
        """
        Remove the CSV log file from disk.
        """
        if os.path.exists(self.filepath):
            os.remove(self.filepath)
            self.headers_written = False
            self.keys = None
