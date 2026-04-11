import pytest
from wifitracker import trust_store


@pytest.fixture(autouse=True)
def tmp_store(tmp_path, monkeypatch):
    monkeypatch.setattr("wifitracker.trust_store.TRUSTED_FILE", tmp_path / "trusted.json")
    monkeypatch.setattr("wifitracker.trust_store.BLOCKED_FILE", tmp_path / "blocked.json")
    monkeypatch.setattr("wifitracker.trust_store.DATA_DIR", tmp_path)


def test_add_and_is_trusted():
    trust_store.add_trusted("AA:BB:CC:DD:EE:FF", name="My Phone")
    assert trust_store.is_trusted("AA:BB:CC:DD:EE:FF") is True


def test_mac_normalized_to_uppercase():
    trust_store.add_trusted("aa:bb:cc:dd:ee:ff")
    assert trust_store.is_trusted("AA:BB:CC:DD:EE:FF") is True


def test_remove_trusted():
    trust_store.add_trusted("AA:BB:CC:DD:EE:FF")
    assert trust_store.remove_trusted("AA:BB:CC:DD:EE:FF") is True
    assert trust_store.is_trusted("AA:BB:CC:DD:EE:FF") is False


def test_add_and_is_blocked():
    trust_store.add_blocked("FF:EE:DD:CC:BB:AA", reason="test")
    assert trust_store.is_blocked("FF:EE:DD:CC:BB:AA") is True


def test_remove_blocked():
    trust_store.add_blocked("FF:EE:DD:CC:BB:AA")
    assert trust_store.remove_blocked("FF:EE:DD:CC:BB:AA") is True
    assert trust_store.is_blocked("FF:EE:DD:CC:BB:AA") is False
