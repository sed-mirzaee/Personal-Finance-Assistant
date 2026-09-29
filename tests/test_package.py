"""Tests for the public API exposed in __init__.py."""

import personal_finance_assistant as pfa


def test_public_api_is_importable():
    for name in pfa.__all__:
        assert hasattr(pfa, name), f"{name} is listed in __all__ but not importable"


def test_top_level_import_works():
    from personal_finance_assistant import Transaction, predict_balance, read_csv

    assert callable(read_csv)
    assert callable(predict_balance)
    assert Transaction is pfa.Transaction