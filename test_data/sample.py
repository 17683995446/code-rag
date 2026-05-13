"""Sample Python module for testing the code RAG system."""

import os
from typing import List, Dict, Optional


class DataProcessor:
    """A class for processing data."""

    def __init__(self, name: str):
        self.name = name
        self.data: List[int] = []

    def add(self, value: int) -> None:
        """Add a value to the data list."""
        self.data.append(value)

    def get_sum(self) -> int:
        """Calculate the sum of all values."""
        total = 0
        for item in self.data:
            total += item
        return total

    def clear(self) -> None:
        """Clear all data."""
        self.data.clear()


def calculate_average(numbers: List[float]) -> Optional[float]:
    """Calculate the average of a list of numbers."""
    if not numbers:
        return None
    return sum(numbers) / len(numbers)


async def fetch_data(url: str) -> Dict:
    """Fetch data from a URL asynchronously."""
    return {"url": url, "status": "ok"}


def process_files(file_paths: List[str]) -> List[str]:
    """Process multiple files and return their names."""
    results = []
    for path in file_paths:
        if os.path.exists(path):
            results.append(os.path.basename(path))
    return results
