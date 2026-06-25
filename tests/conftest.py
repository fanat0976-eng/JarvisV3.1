"""Pytest configuration for Jarvis V3.1 tests."""
from pathlib import Path


def pytest_configure(config):
    """Create workspace directory if it doesn't exist."""
    workspace = Path("workspace")
    workspace.mkdir(exist_ok=True)
