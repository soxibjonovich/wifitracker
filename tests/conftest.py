import pytest


@pytest.fixture(autouse=True)
def tmp_data_dir(tmp_path, monkeypatch):
    """Keep every test away from the real ~/.wifitracker."""
    for module in ("wifitracker.trust_store", "wifitracker.limits"):
        monkeypatch.setattr(f"{module}.DATA_DIR", tmp_path)
    monkeypatch.setattr("wifitracker.trust_store.TRUSTED_FILE", tmp_path / "trusted.json")
    monkeypatch.setattr("wifitracker.trust_store.BLOCKED_FILE", tmp_path / "blocked.json")
    monkeypatch.setattr("wifitracker.limits.LIMITS_FILE", tmp_path / "limits.json")
    monkeypatch.setattr("wifitracker.limits.USAGE_FILE", tmp_path / "usage.json")
    return tmp_path
