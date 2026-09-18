"""Train the MindTrail synthetic wellbeing trend classifier.

This model is for a hackathon demonstration. It is not a medical device and must
not be used to diagnose students or make automated care decisions.
"""

from __future__ import annotations

import csv
import json
import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import torch
from torch import nn


ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "data" / "ml" / "wellbeing_6_months_40_users.csv"
MODEL_PATH = ROOT / "models" / "wellbeing_trend_model.pt"
METADATA_PATH = ROOT / "models" / "wellbeing_trend_model.json"
LABELS = ["stable", "watch", "elevated"]
FEATURES = [
    "mood_mean_7d",
    "stress_mean_7d",
    "sleep_mean_7d",
    "energy_mean_7d",
    "connectedness_mean_7d",
    "mood_slope_7d",
    "stress_slope_7d",
    "sleep_slope_7d",
    "energy_slope_7d",
    "connectedness_slope_7d",
    "mood_std_7d",
    "stress_std_7d",
    "completion_rate_7d",
]


class WellbeingMLP(nn.Module):
    def __init__(self, input_size: int, hidden_size: int = 48) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.15),
            nn.Linear(hidden_size, 24),
            nn.ReLU(),
            nn.Linear(24, len(LABELS)),
        )

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        return self.network(values)


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def std(values: list[float]) -> float:
    average = mean(values)
    return (sum((value - average) ** 2 for value in values) / len(values)) ** 0.5


def slope(values: list[float]) -> float:
    center = (len(values) - 1) / 2
    denominator = sum((index - center) ** 2 for index in range(len(values)))
    return sum((index - center) * (value - mean(values)) for index, value in enumerate(values)) / denominator


def load_samples() -> tuple[list[list[float]], list[int], list[str]]:
    by_user: dict[str, list[dict[str, str]]] = defaultdict(list)
    with DATASET_PATH.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            by_user[row["username"]].append(row)

    samples: list[list[float]] = []
    labels: list[int] = []
    owners: list[str] = []
    metrics = ["mood", "stress", "sleep_hours", "energy", "connectedness"]
    for username, rows in by_user.items():
        rows.sort(key=lambda row: row["date"])
        for end in range(6, len(rows)):
            window = rows[end - 6 : end + 1]
            series = {metric: [float(row[metric]) for row in window] for metric in metrics}
            features = [mean(series[metric]) for metric in metrics]
            features += [slope(series[metric]) for metric in metrics]
            features += [std(series["mood"]), std(series["stress"])]
            features += [mean([float(row["checkin_completed"]) for row in window])]
            samples.append(features)
            labels.append(LABELS.index(rows[end]["risk_label"]))
            owners.append(username)
    return samples, labels, owners


def macro_f1(targets: torch.Tensor, predictions: torch.Tensor) -> float:
    scores = []
    for label in range(len(LABELS)):
        true_positive = int(((targets == label) & (predictions == label)).sum())
        false_positive = int(((targets != label) & (predictions == label)).sum())
        false_negative = int(((targets == label) & (predictions != label)).sum())
        precision = true_positive / max(true_positive + false_positive, 1)
        recall = true_positive / max(true_positive + false_negative, 1)
        scores.append(2 * precision * recall / max(precision + recall, 1e-9))
    return sum(scores) / len(scores)


def main() -> None:
    random.seed(2801)
    torch.manual_seed(2801)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(2801)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    samples, labels, owners = load_samples()
    all_users = sorted(set(owners))
    random.shuffle(all_users)
    test_users = set(all_users[-8:])
    train_indices = [index for index, owner in enumerate(owners) if owner not in test_users]
    test_indices = [index for index, owner in enumerate(owners) if owner in test_users]

    x = torch.tensor(samples, dtype=torch.float32)
    y = torch.tensor(labels, dtype=torch.long)
    train_x, train_y = x[train_indices], y[train_indices]
    test_x, test_y = x[test_indices], y[test_indices]
    feature_mean = train_x.mean(dim=0)
    feature_std = train_x.std(dim=0).clamp_min(1e-6)
    train_x = (train_x - feature_mean) / feature_std
    test_x = (test_x - feature_mean) / feature_std

    counts = torch.bincount(train_y, minlength=len(LABELS)).float()
    class_weights = counts.sum() / (len(LABELS) * counts.clamp_min(1))
    model = WellbeingMLP(len(FEATURES)).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.003, weight_decay=0.001)
    criterion = nn.CrossEntropyLoss(weight=class_weights.to(device))
    train_x, train_y = train_x.to(device), train_y.to(device)

    for epoch in range(180):
        model.train()
        permutation = torch.randperm(len(train_x), device=device)
        for start in range(0, len(train_x), 512):
            indexes = permutation[start : start + 512]
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(train_x[indexes]), train_y[indexes])
            loss.backward()
            optimizer.step()
        if epoch in {0, 59, 119, 179}:
            print(f"epoch={epoch + 1} loss={loss.item():.4f} device={device}")

    model.eval()
    with torch.inference_mode():
        logits = model(test_x.to(device)).cpu()
        predictions = logits.argmax(dim=1)
        accuracy = float((predictions == test_y).float().mean())
        f1 = macro_f1(test_y, predictions)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "state_dict": model.cpu().state_dict(),
            "input_size": len(FEATURES),
            "hidden_size": 48,
            "feature_mean": feature_mean.tolist(),
            "feature_std": feature_std.tolist(),
            "feature_names": FEATURES,
            "labels": LABELS,
        },
        MODEL_PATH,
    )
    metadata = {
        "model_version": "mindtrail-synthetic-v1",
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "device": str(device),
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "dataset_rows": 7200,
        "training_samples": len(train_indices),
        "test_samples": len(test_indices),
        "held_out_users": sorted(test_users),
        "accuracy": round(accuracy, 4),
        "macro_f1": round(f1, 4),
        "labels": LABELS,
        "features": FEATURES,
        "limitations": "Synthetic-data demonstration only; not diagnostic or suitable for automated care decisions.",
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
