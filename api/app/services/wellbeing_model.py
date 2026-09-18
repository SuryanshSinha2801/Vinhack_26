from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import torch
from torch import nn

from api.app.schemas.dashboard import DailyWellbeingRecord, WellbeingInsight


ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = ROOT / "models" / "wellbeing_trend_model.pt"
METADATA_PATH = ROOT / "models" / "wellbeing_trend_model.json"
DISCLAIMER = "Demo trend indicator based on synthetic data. It is not a diagnosis or a replacement for professional support."


class WellbeingMLP(nn.Module):
    def __init__(self, input_size: int, hidden_size: int = 48) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.15),
            nn.Linear(hidden_size, 24),
            nn.ReLU(),
            nn.Linear(24, 3),
        )

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        return self.network(values)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _std(values: list[float]) -> float:
    average = _mean(values)
    return (sum((value - average) ** 2 for value in values) / len(values)) ** 0.5


def _slope(values: list[float]) -> float:
    center = (len(values) - 1) / 2
    denominator = sum((index - center) ** 2 for index in range(len(values)))
    return sum((index - center) * (value - _mean(values)) for index, value in enumerate(values)) / max(denominator, 1)


def build_features(history: list[DailyWellbeingRecord]) -> list[float] | None:
    if len(history) < 7:
        return None
    window = sorted(history, key=lambda item: item.date)[-7:]
    series = {
        "mood": [item.mood for item in window],
        "stress": [item.stress for item in window],
        "sleep": [item.sleep_hours for item in window],
        "energy": [item.energy for item in window],
        "connectedness": [item.connectedness for item in window],
    }
    features = [_mean(values) for values in series.values()]
    features += [_slope(values) for values in series.values()]
    features += [_std(series["mood"]), _std(series["stress"])]
    features += [_mean([float(item.checkin_completed) for item in window])]
    return features


@lru_cache(maxsize=1)
def load_model() -> tuple[WellbeingMLP, dict, dict] | None:
    if not MODEL_PATH.exists() or not METADATA_PATH.exists():
        return None
    checkpoint = torch.load(MODEL_PATH, map_location="cpu", weights_only=True)
    model = WellbeingMLP(checkpoint["input_size"], checkpoint["hidden_size"])
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    return model, checkpoint, metadata


def predict_wellbeing(history: list[DailyWellbeingRecord]) -> WellbeingInsight | None:
    features = build_features(history)
    loaded = load_model()
    if features is None or loaded is None:
        return None
    model, checkpoint, metadata = loaded
    values = torch.tensor([features], dtype=torch.float32)
    mean = torch.tensor(checkpoint["feature_mean"], dtype=torch.float32)
    std = torch.tensor(checkpoint["feature_std"], dtype=torch.float32)
    with torch.inference_mode():
        probabilities = torch.softmax(model((values - mean) / std), dim=1)[0]
    index = int(probabilities.argmax())
    level = checkpoint["labels"][index]
    risk_score = int(round(float(probabilities[1] * 50 + probabilities[2] * 100)))
    window = sorted(history, key=lambda item: item.date)[-7:]
    factors: list[str] = []
    if _mean([item.stress for item in window]) >= 3.5:
        factors.append("Stress has been higher over the last seven days")
    if _mean([item.mood for item in window]) <= 2.7:
        factors.append("Mood has been lower over the last seven days")
    if _mean([item.sleep_hours for item in window]) < 6.5:
        factors.append("Average sleep has been below 6.5 hours")
    if _slope([item.stress for item in window]) > 0.12:
        factors.append("Stress has been trending upward")
    if not factors:
        factors.append("Recent mood, stress, sleep, and energy are broadly steady")
    summaries = {
        "stable": "Your recent pattern looks broadly steady.",
        "watch": "Some recent signals may be worth paying attention to.",
        "elevated": "Several recent signals suggest checking in with support could help.",
    }
    suggestions_by_level = {
        "stable": [
            "Keep one routine that has been helping, such as a regular sleep or meal time.",
            "Continue the short daily check-in so changes are easier to notice.",
        ],
        "watch": [
            "Choose one small reset today: a short walk, slower breathing, or a screen break.",
            "Tell a trusted friend, mentor, or family member how this week has felt.",
            "Consider using the Support page if the pattern continues.",
        ],
        "elevated": [
            "Reach out to a trusted person or counsellor today instead of handling this alone.",
            "Use the Support page to review immediate and professional support options.",
            "If you may be in immediate danger, contact local emergency services now.",
        ],
    }
    return WellbeingInsight(
        level=level,
        score=risk_score,
        confidence=round(float(probabilities[index]), 3),
        summary=summaries[level],
        factors=factors[:3],
        suggestions=suggestions_by_level[level],
        model_version=metadata["model_version"],
        disclaimer=DISCLAIMER,
    )
