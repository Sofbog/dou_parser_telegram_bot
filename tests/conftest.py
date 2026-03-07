"""Shared fixtures for the test suite."""

import sys
from pathlib import Path

import pytest

# Ensure the project root is on sys.path so imports work.
sys.path.insert(0, str(Path(__file__).parent.parent))
