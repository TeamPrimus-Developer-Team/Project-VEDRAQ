#!/usr/bin/env python3
"""
VEDRAQ — Evacuation ML Training Script (Phase 4)
==============================================
Generates synthetic disaster training dataset (2,500 samples across 6 disaster conditions),
splits into 80% train and 20% validation, trains a Gradient Boosted Decision Tree (GBDT)
ensemble regressor, evaluates regression and classification metrics, and persists
the model and evaluation report to backend/app/models/.
"""

import sys
import json
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.services.evacuation_ml import (
    train_and_persist_model,
    MODEL_FILE,
    EVAL_FILE,
    FEATURE_NAMES,
)


def main():
    print("==================================================================")
    print(" VEDRAQ — ADAPTIVE AI EVACUATION MODEL TRAINING PIPELINE")
    print("==================================================================")
    print("Generating synthetic multi-hazard disaster dataset (2,500 samples)...")
    print("Disaster Scenarios: Flood, Earthquake, Cyclone, Landslide, Infra Failure, Comms Blackout")

    eval_metrics = train_and_persist_model(n_samples=2500, seed=42)

    print("\n------------------------------------------------------------------")
    print(" MODEL EVALUATION RESULTS (20% Validation Split = 500 samples)")
    print("------------------------------------------------------------------")

    reg = eval_metrics.get("regression", {})
    print(f"Regression Metrics:")
    print(f"  • Mean Absolute Error (MAE):    {reg.get('mae', 'N/A'):.2f} pts")
    print(f"  • Root Mean Squared Error (RMSE): {reg.get('rmse', 'N/A'):.2f} pts")
    print(f"  • Coefficient of Determ. (R²):   {reg.get('r2', 'N/A'):.4f}")

    cls = eval_metrics.get("classification", {})
    print(f"\nClassification Metrics (Risk Level):")
    print(f"  • Accuracy:                    {cls.get('accuracy', 0)*100:.2f}%")
    print(f"  • Macro F1-Score:              {cls.get('macro_f1', 0):.4f}")

    print("\nPer-Class Breakdown:")
    for c, stats in cls.get("per_class", {}).items():
        print(f"  • {c:<10} | Precision: {stats['precision']:.3f} | Recall: {stats['recall']:.3f} | F1: {stats['f1']:.3f} | Support: {stats['support']}")

    print("\nConfusion Matrix:")
    matrix = cls.get("confusion_matrix", {})
    classes = ["CRITICAL", "HIGH", "MODERATE", "LOWER"]
    header = f"{'True / Pred':<12} " + " ".join(f"{c:>9}" for c in classes)
    print(header)
    print("-" * len(header))
    for true_c in classes:
        row = f"{true_c:<12} " + " ".join(f"{matrix.get(true_c, {}).get(pred_c, 0):>9}" for pred_c in classes)
        print(row)

    print("\n------------------------------------------------------------------")
    print(f" Model saved to:      {MODEL_FILE}")
    print(f" Evaluation saved to: {EVAL_FILE}")
    print("==================================================================")


if __name__ == "__main__":
    main()
