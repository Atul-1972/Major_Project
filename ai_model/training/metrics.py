"""Fixed-order classification metrics with explicit undefined values."""

import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve


def classification_metrics(labels, scores, classes):
    labels = np.asarray(labels, dtype=np.int64)
    scores = np.asarray(scores, dtype=np.float64)
    count = len(classes)
    if labels.ndim != 1 or not len(labels) or scores.shape != (len(labels), count):
        raise ValueError("Invalid labels/scores shape")
    if np.any(labels < 0) or np.any(labels >= count) or not np.isfinite(scores).all():
        raise ValueError("Invalid labels or nonfinite scores")
    if np.any(scores < 0) or np.any(scores > 1) or not np.allclose(scores.sum(axis=1), 1, atol=1e-5):
        raise ValueError("Metrics require normalized model scores")
    predictions = scores.argmax(axis=1)
    matrix = np.bincount(labels * count + predictions, minlength=count * count).reshape(count, count)
    per_class, curves = {}, {}
    divide = lambda numerator, denominator: float(numerator / denominator) if denominator else None
    for index, code in enumerate(classes):
        tp = int(matrix[index, index])
        fn = int(matrix[index].sum()) - tp
        fp = int(matrix[:, index].sum()) - tp
        tn = len(labels) - tp - fn - fp
        positive = labels == index
        auc = None
        reason = None
        if positive.any() and not positive.all():
            auc = float(roc_auc_score(positive, scores[:, index]))
            fpr, tpr, _ = roc_curve(positive, scores[:, index])
            curves[code] = {"fpr": fpr.tolist(), "tpr": tpr.tolist()}
        else:
            reason = "ROC-AUC requires both positive and negative examples"
        per_class[code] = {
            "precision": divide(tp, tp + fp), "sensitivity": divide(tp, tp + fn),
            "specificity": divide(tn, tn + fp), "f1": divide(2 * tp, 2 * tp + fp + fn),
            "support": tp + fn, "roc_auc": auc, "roc_auc_unavailable_reason": reason,
            "tp": tp, "fn": fn, "fp": fp, "tn": tn,
        }
    mean_defined = lambda field: float(np.mean([item[field] for item in per_class.values() if item[field] is not None])) if any(item[field] is not None for item in per_class.values()) else None
    return {
        "images": len(labels), "class_order": list(classes), "confusion_matrix": matrix.tolist(),
        "accuracy": float(np.trace(matrix) / len(labels)), "macro_f1": mean_defined("f1"),
        "balanced_accuracy": mean_defined("sensitivity"), "macro_roc_auc": mean_defined("roc_auc"),
        "per_class": per_class, "roc_curves": curves,
        "undefined_metric_policy": "null when the denominator is zero; macro averages use defined classes only",
        "score_interpretation": "Uncalibrated softmax model scores, not clinical risk probabilities",
    }


def save_figures(metrics, history, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output.mkdir(parents=True, exist_ok=True)
    matrix = np.asarray(metrics["confusion_matrix"])
    fig, ax = plt.subplots(figsize=(8, 7))
    display = ax.imshow(matrix, cmap="Blues")
    ax.set(xticks=range(len(matrix)), yticks=range(len(matrix)), xticklabels=metrics["class_order"], yticklabels=metrics["class_order"], xlabel="Predicted", ylabel="Source label", title="E1 held-out test confusion matrix")
    for row in range(len(matrix)):
        for column in range(len(matrix)):
            ax.text(column, row, str(matrix[row, column]), ha="center", va="center", color="white" if matrix[row, column] > matrix.max() / 2 else "black")
    fig.colorbar(display, ax=ax)
    fig.tight_layout()
    fig.savefig(output / "confusion_matrix.png", dpi=180)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 6))
    for code, curve in metrics["roc_curves"].items():
        ax.plot(curve["fpr"], curve["tpr"], label=f"{code} (AUC {metrics['per_class'][code]['roc_auc']:.3f})")
    ax.plot([0, 1], [0, 1], "k--", alpha=0.4)
    ax.set(xlabel="False positive rate", ylabel="True positive rate", title="One-vs-rest ROC")
    if metrics["roc_curves"]:
        ax.legend()
    fig.tight_layout()
    fig.savefig(output / "roc_curves.png", dpi=180)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    epochs = [item["epoch"] + 1 for item in history]
    axes[0].plot(epochs, [item["train_loss"] for item in history], label="Weighted training CE")
    axes[0].plot(epochs, [item["validation_loss"] for item in history], label="Unweighted validation CE")
    axes[0].set(xlabel="Epoch", ylabel="Loss")
    axes[0].legend()
    axes[1].plot(epochs, [item["validation_macro_f1"] for item in history])
    axes[1].set(xlabel="Epoch", ylabel="Validation macro-F1")
    fig.tight_layout()
    fig.savefig(output / "training_curves.png", dpi=180)
    plt.close(fig)
