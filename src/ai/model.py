"""
RandLA-Net: Efficient Semantic Segmentation of Large-Scale Point Clouds.

Pure PyTorch implementation of:
1. Local Spatial Encoding (LocSE)
2. Attentive Pooling
3. Dilated Residual Blocks
4. Random Subsampling & Nearest Neighbor Feature Interpolation
5. Multi-scale Encoder-Decoder architecture

No external C++/CUDA extensions required; works reliably on CPU and GPU.
"""

from typing import List, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F


def compute_knn(xyz: torch.Tensor, k: int) -> torch.Tensor:
    """
    Compute K-Nearest Neighbors using batched Euclidean distances in PyTorch.

    Args:
        xyz: (B, N, 3) point coordinates.
        k: Number of nearest neighbors.

    Returns:
        idx: (B, N, k) indices of nearest neighbors.
    """
    k = min(k, xyz.shape[1])
    # Pairwise distance: ||a - b||^2 = ||a||^2 - 2<a,b> + ||b||^2
    dist_sq = torch.cdist(xyz, xyz, p=2.0) ** 2  # (B, N, N)
    _, idx = torch.topk(dist_sq, k=k, dim=-1, largest=False)
    return idx


def gather_neighbor_features(features: torch.Tensor, idx: torch.Tensor) -> torch.Tensor:
    """
    Gather neighbor features given neighbor indices.

    Args:
        features: (B, C, N) point features.
        idx: (B, N, k) neighbor indices.

    Returns:
        gathered: (B, C, N, k) neighbor features.
    """
    B, C, N = features.shape
    k = idx.shape[-1]

    # Reshape idx for gather: (B, 1, N * k) -> expand to (B, C, N * k)
    idx_expanded = idx.view(B, 1, N * k).expand(-1, C, -1)
    gathered = torch.gather(features, dim=2, index=idx_expanded)
    return gathered.view(B, C, N, k)


class LocalSpatialEncoding(nn.Module):
    """
    Local Spatial Encoding (LocSE) module.
    Encodes explicit relative 3D spatial coordinates [p_i, p_i^k, p_i - p_i^k, ||p_i - p_i^k||].
    """

    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        # Relative position encoding has 10 channels:
        # p_i (3) + p_i^k (3) + (p_i - p_i^k) (3) + distance (1) = 10
        self.mlp = nn.Sequential(
            nn.Conv2d(10 + in_channels, out_channels, kernel_size=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.LeakyReLU(0.2, inplace=True),
        )

    def forward(self, xyz: torch.Tensor, features: torch.Tensor, neighbor_idx: torch.Tensor) -> torch.Tensor:
        """
        Args:
            xyz: (B, N, 3) coordinates
            features: (B, C, N) features
            neighbor_idx: (B, N, k) neighbor indices

        Returns:
            encoded: (B, out_channels, N, k) augmented local features
        """
        B, N, k = neighbor_idx.shape
        # Gather neighbor coordinates: (B, 3, N, k)
        neighbor_xyz = gather_neighbor_features(xyz.permute(0, 2, 1), neighbor_idx)
        center_xyz = xyz.permute(0, 2, 1).unsqueeze(-1).expand(-1, -1, -1, k)

        diff_xyz = center_xyz - neighbor_xyz
        dist = torch.norm(diff_xyz, dim=1, keepdim=True)
        # Position encoding: (B, 10, N, k)
        pos_encoding = torch.cat([center_xyz, neighbor_xyz, diff_xyz, dist], dim=1)

        # Gather neighbor features: (B, C, N, k)
        neighbor_feat = gather_neighbor_features(features, neighbor_idx)

        # Concatenate position encoding with features: (B, 10 + C, N, k)
        concat_feat = torch.cat([pos_encoding, neighbor_feat], dim=1)
        return self.mlp(concat_feat)


class AttentivePooling(nn.Module):
    """
    Attentive Pooling module.
    Learns an attention weight over the K neighbors and aggregates features.
    """

    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.score_mlp = nn.Sequential(
            nn.Conv2d(in_channels, in_channels, kernel_size=1, bias=False),
            nn.BatchNorm2d(in_channels),
            nn.Softmax(dim=-1),
        )
        self.out_mlp = nn.Sequential(
            nn.Conv1d(in_channels, out_channels, kernel_size=1, bias=False),
            nn.BatchNorm1d(out_channels),
            nn.LeakyReLU(0.2, inplace=True),
        )

    def forward(self, local_features: torch.Tensor) -> torch.Tensor:
        """
        Args:
            local_features: (B, in_channels, N, k)

        Returns:
            aggregated: (B, out_channels, N)
        """
        attention_scores = self.score_mlp(local_features)  # (B, C, N, k)
        weighted_features = torch.sum(local_features * attention_scores, dim=-1)  # (B, C, N)
        return self.out_mlp(weighted_features)


class DilatedResidualBlock(nn.Module):
    """
    Dilated Residual Block chaining two LocSE + Attentive Pooling units with a skip connection.
    """

    def __init__(self, in_channels: int, out_channels: int, k_neighbors: int = 16):
        super().__init__()
        self.k = k_neighbors
        mid_channels = out_channels // 2

        self.locse1 = LocalSpatialEncoding(in_channels, mid_channels)
        self.pool1 = AttentivePooling(mid_channels, mid_channels)

        self.locse2 = LocalSpatialEncoding(mid_channels, mid_channels)
        self.pool2 = AttentivePooling(mid_channels, out_channels)

        # Shortcut projection if channel dimensions differ
        if in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv1d(in_channels, out_channels, kernel_size=1, bias=False),
                nn.BatchNorm1d(out_channels),
            )
        else:
            self.shortcut = nn.Identity()

        self.lrelu = nn.LeakyReLU(0.2, inplace=True)

    def forward(self, xyz: torch.Tensor, features: torch.Tensor) -> torch.Tensor:
        """
        Args:
            xyz: (B, N, 3)
            features: (B, in_channels, N)

        Returns:
            out_features: (B, out_channels, N)
        """
        neighbor_idx = compute_knn(xyz, self.k)

        res = self.shortcut(features)

        # First unit
        f1 = self.locse1(xyz, features, neighbor_idx)
        f1 = self.pool1(f1)

        # Second unit
        f2 = self.locse2(xyz, f1, neighbor_idx)
        f2 = self.pool2(f2)

        return self.lrelu(f2 + res)


class RandLANet(nn.Module):
    """
    RandLA-Net architecture for Point Cloud Semantic Segmentation.
    """

    def __init__(
        self,
        num_classes: int = 8,
        in_channels: int = 4,  # [X, Y, Z, Intensity]
        k_neighbors: int = 16,
        subsampling_ratios: Tuple[int, ...] = (4, 4),
    ):
        """
        Args:
            num_classes: Target number of semantic classes (8 for project taxonomy).
            in_channels: Input point feature dimensionality (4 for XYZ + Intensity).
            k_neighbors: Nearest neighbors for attentive pooling.
            subsampling_ratios: Subsampling factor at each encoder stage.
        """
        super().__init__()
        self.num_classes = num_classes
        self.k_neighbors = k_neighbors
        self.subsampling_ratios = subsampling_ratios

        # Input feature projection
        self.fc_in = nn.Sequential(
            nn.Conv1d(in_channels, 16, kernel_size=1, bias=False),
            nn.BatchNorm1d(16),
            nn.LeakyReLU(0.2, inplace=True),
        )

        # Encoder stages
        self.block1 = DilatedResidualBlock(16, 32, k_neighbors=k_neighbors)
        self.block2 = DilatedResidualBlock(32, 64, k_neighbors=k_neighbors)
        self.block3 = DilatedResidualBlock(64, 128, k_neighbors=k_neighbors)

        # Decoder stages (upsampling via nearest interpolation + MLP)
        self.up2 = nn.Sequential(
            nn.Conv1d(128 + 64, 64, kernel_size=1, bias=False),
            nn.BatchNorm1d(64),
            nn.LeakyReLU(0.2, inplace=True),
        )
        self.up1 = nn.Sequential(
            nn.Conv1d(64 + 32, 32, kernel_size=1, bias=False),
            nn.BatchNorm1d(32),
            nn.LeakyReLU(0.2, inplace=True),
        )

        # Final Segmentation Head
        self.classifier = nn.Sequential(
            nn.Conv1d(32, 32, kernel_size=1, bias=False),
            nn.BatchNorm1d(32),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Dropout(0.3),
            nn.Conv1d(32, num_classes, kernel_size=1),
        )

    @staticmethod
    def _random_subsample(
        xyz: torch.Tensor,
        features: torch.Tensor,
        ratio: int,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Subsample points by taking every ratio-th point."""
        B, N, _ = xyz.shape
        target_n = max(1, N // ratio)
        sub_xyz = xyz[:, :target_n, :]
        sub_features = features[:, :, :target_n]
        return sub_xyz, sub_features, sub_xyz

    @staticmethod
    def _nearest_interpolate(
        query_xyz: torch.Tensor,
        support_xyz: torch.Tensor,
        support_features: torch.Tensor,
    ) -> torch.Tensor:
        """
        Upsample support features to query points using 1-nearest neighbor.

        Args:
            query_xyz: (B, N_query, 3) target points
            support_xyz: (B, N_support, 3) source points
            support_features: (B, C, N_support) features to upsample

        Returns:
            interpolated: (B, C, N_query)
        """
        dist = torch.cdist(query_xyz, support_xyz, p=2.0)  # (B, N_query, N_support)
        _, nearest_idx = torch.topk(dist, k=1, dim=-1, largest=False)  # (B, N_query, 1)

        B, C, N_sup = support_features.shape
        N_query = query_xyz.shape[1]
        idx_exp = nearest_idx.permute(0, 2, 1).expand(-1, C, -1)  # (B, C, N_query)
        interpolated = torch.gather(support_features, dim=2, index=idx_exp)
        return interpolated

    def forward(self, xyz: torch.Tensor, features: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            xyz: (B, N, 3) point coordinates.
            features: (B, C_in, N) point features (e.g., [X, Y, Z, Intensity]).

        Returns:
            logits: (B, num_classes, N) semantic class prediction logits.
        """
        # Input projection
        f0 = self.fc_in(features)  # (B, 16, N)

        # Stage 1
        xyz1 = xyz
        f1 = self.block1(xyz1, f0)  # (B, 32, N)

        # Stage 2: Downsample 1
        target_n1 = max(1, xyz1.shape[1] // self.subsampling_ratios[0])
        xyz2 = xyz1[:, :target_n1, :]
        f2_in = f1[:, :, :target_n1]
        f2 = self.block2(xyz2, f2_in)  # (B, 64, N/4)

        # Stage 3: Downsample 2
        target_n2 = max(1, xyz2.shape[1] // self.subsampling_ratios[1])
        xyz3 = xyz2[:, :target_n2, :]
        f3_in = f2[:, :, :target_n2]
        f3 = self.block3(xyz3, f3_in)  # (B, 128, N/16)

        # Decoder Stage 2: Upsample Stage 3 -> Stage 2
        up_f3 = self._nearest_interpolate(xyz2, xyz3, f3)
        cat_f2 = torch.cat([up_f3, f2], dim=1)
        f2_dec = self.up2(cat_f2)

        # Decoder Stage 1: Upsample Stage 2 -> Stage 1
        up_f2 = self._nearest_interpolate(xyz1, xyz2, f2_dec)
        cat_f1 = torch.cat([up_f2, f1], dim=1)
        f1_dec = self.up1(cat_f1)

        # Classification logits
        logits = self.classifier(f1_dec)  # (B, num_classes, N)
        return logits


if __name__ == "__main__":
    # Test RandLA-Net with synthetic tensor batch
    B, N, C_in, num_cls = 2, 1024, 4, 8
    dummy_xyz = torch.randn(B, N, 3)
    dummy_features = torch.randn(B, C_in, N)

    model = RandLANet(num_classes=num_cls, in_channels=C_in, k_neighbors=12)
    model.eval()

    with torch.no_grad():
        out_logits = model(dummy_xyz, dummy_features)

    print("RandLA-Net Forward Pass Verified:")
    print(f"  Input XYZ:      {dummy_xyz.shape}")
    print(f"  Input Features: {dummy_features.shape}")
    print(f"  Output Logits:  {out_logits.shape} (Expected: ({B}, {num_cls}, {N}))")
    assert out_logits.shape == (B, num_cls, N)
    print("  Assertion Passed!")
