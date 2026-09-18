import csv
import json
from pathlib import Path


def test_synthetic_dataset_has_40_users_and_180_days_each() -> None:
    path = Path("data/ml/wellbeing_6_months_40_users.csv")
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    usernames = {row["username"] for row in rows}
    counts = {username: sum(row["username"] == username for row in rows) for username in usernames}
    assert len(rows) == 7200
    assert len(usernames) == 40
    assert set(counts.values()) == {180}
    assert set(row["risk_label"] for row in rows) == {"stable", "watch", "elevated"}


def test_trained_model_metadata_records_gpu_and_user_holdout() -> None:
    metadata = json.loads(Path("models/wellbeing_trend_model.json").read_text(encoding="utf-8"))
    assert metadata["device"] == "cuda"
    assert "RTX 5060" in metadata["gpu"]
    assert len(metadata["held_out_users"]) == 8
    assert metadata["test_samples"] > 0
