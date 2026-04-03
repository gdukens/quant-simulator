import os
import sys
import pytest

# Ensure local package path is included
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'hf_space_bundle')))

from quantlib_api import QuantLibClient


def test_quantlibclient_prefers_constructor_api_key_over_env(monkeypatch):
    monkeypatch.setenv('QUANTLIB_API_KEY', 'env-key')

    client = QuantLibClient(api_key='constructor-key')

    assert client._api_key == 'constructor-key'


def test_quantlibclient_uses_env_api_key_if_constructor_missing(monkeypatch):
    monkeypatch.setenv('QUANTLIB_API_KEY', 'env-key')

    client = QuantLibClient()

    assert client._api_key == 'env-key'


def test_quantlibclient_authentication_token_using_api_key():
    client = QuantLibClient(api_key='dummy-api-key')
    assert client.is_authenticated
