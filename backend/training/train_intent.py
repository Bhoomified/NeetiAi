"""
Fine-tune the DistilBERT intent classifier on the expanded intent set.

Starts from the existing local checkpoint (encoder weights already adapted to
this domain) and swaps in a fresh classification head sized for the new
label set — no network download needed.

Run from backend/:
    venv/bin/python -m training.train_intent
"""
import os
import json
import shutil
import random
from datetime import datetime

import joblib
import numpy as np
import torch
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from training.intent_data import HANDWRITTEN_TEST, INTENTS, generate

ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "ml", "artifacts")
MODEL_DIR = os.path.join(ARTIFACT_DIR, "distilbert_intent")
ENCODER_PATH = os.path.join(ARTIFACT_DIR, "intent_label_encoder.pkl")
METRICS_PATH = os.path.join(ARTIFACT_DIR, "intent_metrics.json")
BACKUP_DIR = MODEL_DIR + "_backup"

EPOCHS = 4
BATCH_SIZE = 32
LR = 3e-5
MAX_LEN = 32
SEED = 42


def pick_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def predict(model, tokenizer, texts, device):
    model.eval()
    preds = []
    with torch.no_grad():
        for i in range(0, len(texts), 64):
            batch = tokenizer(texts[i:i + 64], return_tensors="pt", padding=True, truncation=True, max_length=MAX_LEN)
            batch = {k: v.to(device) for k, v in batch.items()}
            preds.extend(model(**batch).logits.argmax(-1).cpu().tolist())
    return preds


def main():
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    device = pick_device()
    print(f"device: {device}")

    rows = generate(per_intent=400, seed=SEED)
    texts = [t for t, _ in rows]
    labels = [l for _, l in rows]

    encoder = LabelEncoder().fit(INTENTS)
    y = encoder.transform(labels)
    X_train, X_val, y_train, y_val = train_test_split(texts, y, test_size=0.15, stratify=y, random_state=SEED)
    print(f"train={len(X_train)} val={len(X_val)} handwritten_test={len(HANDWRITTEN_TEST)}")

    # Always start from the original v1 checkpoint (backed up on first run) so
    # retraining is reproducible rather than stacking on previous fine-tunes.
    base_dir = BACKUP_DIR if os.path.exists(BACKUP_DIR) else MODEL_DIR
    tokenizer = AutoTokenizer.from_pretrained(base_dir)
    model = AutoModelForSequenceClassification.from_pretrained(
        base_dir,
        num_labels=len(INTENTS),
        id2label={i: l for i, l in enumerate(encoder.classes_)},
        label2id={l: i for i, l in enumerate(encoder.classes_)},
        ignore_mismatched_sizes=True,
    ).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)
    steps_total = EPOCHS * ((len(X_train) + BATCH_SIZE - 1) // BATCH_SIZE)
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda s: max(0.0, 1 - s / steps_total))

    for epoch in range(EPOCHS):
        model.train()
        order = np.random.permutation(len(X_train))
        total_loss = 0.0
        for i in range(0, len(order), BATCH_SIZE):
            idx = order[i:i + BATCH_SIZE]
            batch = tokenizer([X_train[j] for j in idx], return_tensors="pt", padding=True, truncation=True, max_length=MAX_LEN)
            batch = {k: v.to(device) for k, v in batch.items()}
            out = model(**batch, labels=torch.tensor(y_train[idx], device=device))
            out.loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
            total_loss += out.loss.item() * len(idx)
        val_f1 = f1_score(y_val, predict(model, tokenizer, X_val, device), average="macro")
        print(f"epoch {epoch + 1}/{EPOCHS}  loss={total_loss / len(X_train):.4f}  val_macro_f1={val_f1:.4f}")

    val_pred = predict(model, tokenizer, X_val, device)
    hw_texts = [t for t, _ in HANDWRITTEN_TEST]
    hw_true = encoder.transform([l for _, l in HANDWRITTEN_TEST])
    hw_pred = predict(model, tokenizer, hw_texts, device)

    print("\n=== handwritten (unseen phrasing) test ===")
    print(classification_report(hw_true, hw_pred, target_names=encoder.classes_, zero_division=0))
    for text, t, p in zip(hw_texts, hw_true, hw_pred):
        if t != p:
            print(f"  MISS  {text!r}: expected {encoder.classes_[t]}, got {encoder.classes_[p]}")

    metrics = {
        "trained_at": datetime.now().isoformat(timespec="seconds"),
        "intents": list(encoder.classes_),
        "train_size": len(X_train),
        "val_macro_f1": round(float(f1_score(y_val, val_pred, average="macro")), 4),
        "handwritten_macro_f1": round(float(f1_score(hw_true, hw_pred, average="macro")), 4),
        "handwritten_accuracy": round(float(np.mean(np.array(hw_true) == np.array(hw_pred))), 4),
    }
    print(json.dumps(metrics, indent=2))

    if not os.path.exists(BACKUP_DIR):
        shutil.copytree(MODEL_DIR, BACKUP_DIR)
        shutil.copy(ENCODER_PATH, os.path.join(BACKUP_DIR, "intent_label_encoder.pkl"))
        print(f"backed up previous model to {BACKUP_DIR}")

    model.to("cpu").save_pretrained(MODEL_DIR)
    tokenizer.save_pretrained(MODEL_DIR)
    joblib.dump(encoder, ENCODER_PATH)
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"saved model to {MODEL_DIR}")


if __name__ == "__main__":
    main()
