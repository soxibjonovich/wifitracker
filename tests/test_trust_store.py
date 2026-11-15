import json

import pytest
from wifitracker import trust_store


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


@pytest.mark.parametrize("raw", ["aa-bb-cc-dd-ee-ff", "AA:BB:CC:DD:EE:FF", "aabb.ccdd.eeff", "AABBCCDDEEFF"])
def test_normalize_mac_formats(raw):
    assert trust_store.normalize_mac(raw) == "AA:BB:CC:DD:EE:FF"


def test_normalize_mac_rejects_garbage():
    with pytest.raises(ValueError):
        trust_store.normalize_mac("not-a-mac")


def test_dash_and_colon_macs_match():
    trust_store.add_trusted("aa-bb-cc-dd-ee-ff")
    assert trust_store.is_trusted("AA:BB:CC:DD:EE:FF") is True


def test_old_files_with_dash_keys_still_match(tmp_data_dir):
    (tmp_data_dir / "blocked.json").write_text(json.dumps({"AA-BB-CC-DD-EE-FF": {"reason": "old"}}))
    assert trust_store.is_blocked("aa:bb:cc:dd:ee:ff") is True
