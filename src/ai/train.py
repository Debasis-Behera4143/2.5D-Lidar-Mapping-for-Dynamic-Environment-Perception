"""
Training and Validation Pipeline for RandLA-Net on SemanticKITTI.

Features:
- Separate training and validation loops with zero data leakage
- Tracks Training Loss, Validation Loss, Overall Accuracy, Precision, Recall, Per-class IoU, mIoU
- Formatted Confusion Matrix output
- Checkpoint saving based on validation mIoU
- Support for official SemanticKITTI dataset directory layout
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR

from src.data.dataset import get_train_val_loaders, create_dataloader
from src.ai.model import RandLANet
from src.ai.evaluate import SegmentationEvaluator
from src.ai.label_mapping import NUM_CLASSES, IGNORE_LABEL_ID, PROJECT_CLASSES


def train_one_epoch(
    model: nn.Module,
    loader: torch.utils.data.DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
) -> float:
    """Train model for one epoch and return average training loss."""
    model.train()
    total_loss = 0.0
    num_batches = 0

    for batch in loader:
        xyz = batch["xyz"].to(device)
        features = batch["features"].to(device)
        labels = batch["labels"].to(device)

        optimizer.zero_grad()
        logits = model(xyz, features)  # (B, num_classes, N)
        loss = criterion(logits, labels)
        loss.backward()

        # Gradient clipping for numerical stability
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        total_loss += loss.item()
        num_batches += 1

    return total_loss / max(1, num_batches)


def validate_epoch(
    model: nn.Module,
    loader: torch.utils.data.DataLoader,
    criterion: nn.Module,
    device: torch.device,
    ignore_index: Optional[int] = IGNORE_LABEL_ID,
) -> Tuple[float, Dict[str, Any], SegmentationEvaluator]:
    """Validate model and compute validation loss, per-class metrics, and confusion matrix."""
    model.eval()
    evaluator = SegmentationEvaluator(num_classes=NUM_CLASSES, ignore_index=ignore_index)
    total_val_loss = 0.0
    num_batches = 0

    with torch.no_grad():
        for batch in loader:
            xyz = batch["xyz"].to(device)
            features = batch["features"].to(device)
            labels = batch["labels"].to(device)

            logits = model(xyz, features)
            loss = criterion(logits, labels)
            total_val_loss += loss.item()
            num_batches += 1

            preds = torch.argmax(logits, dim=1)
            evaluator.update(labels.cpu(), preds.cpu())

    avg_val_loss = total_val_loss / max(1, num_batches)
    metrics = evaluator.compute_metrics()
    return avg_val_loss, metrics, evaluator


def run_training(
    dataset_root: str = "data/semantic_kitti",
    train_seq: str = "00",
    val_seq: str = "08",
    epochs: int = 5,
    batch_size: int = 1,
    num_points: int = 2048,
    lr: float = 0.003,
    save_dir: str = "checkpoints",
    checkpoint_name: str = "best_randlanet_real.pt",
) -> Path:
    """
    Execute full training, validation, and checkpointing experiment.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("=" * 75)
    print("STARTING RANDLA-NET REAL-DATA PERCEPTION TRAINING")
    print("=" * 75)
    print(f"Device:           {device}")
    print(f"Dataset Root:     {Path(dataset_root).resolve()}")
    print(f"Train Sequence:   {train_seq}")
    print(f"Val Sequence:     {val_seq}")
    print(f"Target Points:    {num_points} points/scan")
    print(f"Epochs:           {epochs}")
    print(f"Batch Size:       {batch_size}")
    print(f"Learning Rate:    {lr}")
    print("=" * 75)

    # 1. Build train and val dataloaders
    train_loader, val_loader = get_train_val_loaders(
        dataset_root=dataset_root,
        train_sequences=[train_seq],
        val_sequences=[val_seq],
        batch_size=batch_size,
        target_num_points=num_points,
    )

    print(f"Indexed: {len(train_loader.dataset)} training frames, {len(val_loader.dataset)} validation frames.")

    # 2. Model & Optimization
    model = RandLANet(num_classes=NUM_CLASSES, in_channels=4, k_neighbors=12).to(device)
    optimizer = AdamW(model.parameters(), lr=lr, weight_decay=1e-3)
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

    # CrossEntropyLoss: slightly downweight 'other' (class 7) to emphasize road, vehicles, pedestrians
    class_weights = torch.ones(NUM_CLASSES, dtype=torch.float32, device=device)
    class_weights[IGNORE_LABEL_ID] = 0.2  # De-emphasize unannotated/outlier points
    class_weights[4] = 2.0  # Emphasize vehicles
    class_weights[5] = 3.0  # Emphasize pedestrians
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)
    best_ckpt_file = save_path / checkpoint_name

    best_miou = 0.0
    final_evaluator: Optional[SegmentationEvaluator] = None

    for epoch in range(1, epochs + 1):
        train_loss = train_one_epoch(model, train_loader, optimizer, criterion, device)
        scheduler.step()

        val_loss, val_metrics, evaluator = validate_epoch(
            model, val_loader, criterion, device, ignore_index=IGNORE_LABEL_ID
        )
        final_evaluator = evaluator

        miou = val_metrics["mean_iou"] * 100.0
        acc = val_metrics["overall_accuracy"] * 100.0
        prec = val_metrics["macro_precision"] * 100.0
        rec = val_metrics["macro_recall"] * 100.0

        print(
            f"Epoch [{epoch:02d}/{epochs:02d}] | "
            f"Train Loss: {train_loss:.4f} | "
            f"Val Loss: {val_loss:.4f} | "
            f"Val Acc: {acc:>5.2f}% | "
            f"Val mIoU: {miou:>5.2f}% | "
            f"Macro Prec: {prec:>5.2f}% | "
            f"Macro Rec: {rec:>5.2f}%"
        )

        # Save checkpoint if best validation mIoU
        if miou >= best_miou or epoch == 1:
            best_miou = miou
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "train_loss": float(train_loss),
                "val_loss": float(val_loss),
                "val_miou": float(miou),
                "val_accuracy": float(acc),
                "per_class_iou": val_metrics["per_class_iou"],
                "confusion_matrix": val_metrics["confusion_matrix"].tolist(),
                "taxonomy": PROJECT_CLASSES,
            }, str(best_ckpt_file))
            print(f"  --> Saved new best checkpoint: {best_ckpt_file.name} (Val mIoU: {miou:.2f}%)")

    # Display final comprehensive evaluation report and confusion matrix
    if final_evaluator is not None:
        print("\nFinal Epoch Evaluation Report on Real SemanticKITTI Validation Set:")
        final_evaluator.print_report(show_confusion_matrix=True)

    print(f"Training completed. Best checkpoint saved to: {best_ckpt_file.resolve()}")
    return best_ckpt_file


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train RandLA-Net on SemanticKITTI")
    parser.add_argument("--data-root", type=str, default="data/semantic_kitti", help="Dataset root directory")
    parser.add_argument("--train-seq", type=str, default="00", help="Training sequence ID")
    parser.add_argument("--val-seq", type=str, default="08", help="Validation sequence ID")
    parser.add_argument("--epochs", type=int, default=3, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=1, help="Batch size")
    parser.add_argument("--points", type=int, default=2048, help="Points per frame")
    parser.add_argument("--lr", type=float, default=0.003, help="Learning rate")
    args = parser.parse_args()

    run_training(
        dataset_root=args.data_root,
        train_seq=args.train_seq,
        val_seq=args.val_seq,
        epochs=args.epochs,
        batch_size=args.batch_size,
        num_points=args.points,
        lr=args.lr,
    )
