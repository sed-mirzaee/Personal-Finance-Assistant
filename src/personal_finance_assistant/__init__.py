"""Personal Finance Assistant: track transactions, keep an account balance, predict future expenses and get simple suggestions."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("personal-finance-assistant")
except PackageNotFoundError:  # package is not installed
    __version__ = "unknown"