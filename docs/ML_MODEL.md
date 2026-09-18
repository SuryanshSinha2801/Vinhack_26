# MindTrail ML trend model

## Purpose

The model gives the signed-in student a `stable`, `watch`, or `elevated` trend indicator from their latest seven days. It is a hackathon demonstration trained entirely on fictional synthetic data. It is not diagnostic, must not make care decisions, and must not replace a counsellor or emergency support.

## Dataset

- 40 fictional users
- 180 consecutive days per user
- 7,200 raw daily records
- Mood, stress, sleep, energy, connectedness, completion state, support response, and note
- Deterministic generator for reproducible demos
- CSV: `data/ml/wellbeing_6_months_40_users.csv`
- Workbook: `data/demo/mindtrail_demo_6_months.xlsx`

The labels are synthetic rules created only to demonstrate the training and inference pipeline. They are not clinically validated labels.

## Model choice

A compact multilayer perceptron was selected because the input is a small tabular feature vector rather than text, images, or a long sequence. It has two hidden layers (48 and 24 units), ReLU activations, and dropout. This is small enough for fast local inference and still demonstrates GPU training.

The 13 inputs are seven-day averages and slopes for mood, stress, sleep, energy, and connectedness, mood and stress variability, and the completion rate.

## Training and evaluation

- Framework: PyTorch 2.11.0 with CUDA 12.8
- Device: NVIDIA GeForce RTX 5060 Laptop GPU
- Training users: 32
- Held-out test users: 8
- Training samples: 5,568
- Test samples: 1,392
- Test accuracy: 0.6846
- Macro F1: 0.6005

The split is user-based. A held-out user's records never appear in training. This reduces same-user leakage. These metrics measure reconstruction of synthetic labels, not performance on real student wellbeing.

## Files and command

- `ml/train_wellbeing_model.py`: reproducible training code
- `models/wellbeing_trend_model.pt`: weights and normalization values
- `models/wellbeing_trend_model.json`: training metadata and limitations
- `api/app/services/wellbeing_model.py`: backend feature extraction and inference

```powershell
.\.venv\Scripts\python.exe ml\train_wellbeing_model.py
```
