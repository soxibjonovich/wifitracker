from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from wifitracker import limits, trust_store
from wifitracker.main import app

MAC = "AA:BB:CC:DD:EE:FF"
runner = CliRunner()


@pytest.fixture(autouse=True)
def setup_done():
    with patch("wifitracker.main.is_setup_done", return_value=True):
        yield


def test_block_calls_router_and_stores():
    with patch("wifitracker.main.block_device") as block:
        result = runner.invoke(app, ["devices", "block", "aa-bb-cc-dd-ee-ff", "--name", "kid"])
    assert result.exit_code == 0, result.output
    block.assert_called_once_with(MAC, "kid")
    assert trust_store.is_blocked(MAC)


def test_block_router_error_not_stored():
    from tplinkrouterc6u import ClientException
    with patch("wifitracker.main.block_device", side_effect=ClientException("nope")):
        result = runner.invoke(app, ["devices", "block", MAC])
    assert result.exit_code == 1
    assert "nope" in result.output
    assert not trust_store.is_blocked(MAC)


def test_unblock_clears_limit_block():
    limits.set_limit(MAC, 1)
    limits.mark_blocked(MAC)
    with patch("wifitracker.main.unblock_device") as unblock:
        result = runner.invoke(app, ["devices", "unblock", MAC])
    assert result.exit_code == 0, result.output
    unblock.assert_called_once_with(MAC)
    assert not limits.is_limit_blocked(MAC)


def test_invalid_mac_rejected():
    result = runner.invoke(app, ["devices", "block", "zz"])
    assert result.exit_code != 0


def test_limit_unlimit_and_list():
    assert runner.invoke(app, ["devices", "limit", MAC, "2.5", "--name", "tablet"]).exit_code == 0
    assert limits.get_limits()[MAC]["hours"] == 2.5
    result = runner.invoke(app, ["devices", "limits"])
    assert "tablet" in result.output and "2.5h" in result.output
    assert runner.invoke(app, ["devices", "unlimit", MAC]).exit_code == 0
    assert limits.get_limits() == {}
