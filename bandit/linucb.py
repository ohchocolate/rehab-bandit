"""LinUCB contextual bandit skeleton.

Hard Gate: the author implements the runnable LinUCB math in the functions
below. Assistants may maintain structure, tests, docs, and integration code.
"""

from __future__ import annotations

import numpy as np


def compute_theta(A: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Estimate per-arm linear weights from state matrix A and vector b."""
    raise NotImplementedError("Hard gate: author must implement compute_theta")


def predict_mean(theta: np.ndarray, x: np.ndarray) -> float:
    """Predict expected reward for a context vector x."""
    raise NotImplementedError("Hard gate: author must implement predict_mean")


def compute_bonus(A: np.ndarray, x: np.ndarray, alpha: float) -> float:
    """Compute the UCB uncertainty bonus for a context vector x."""
    raise NotImplementedError("Hard gate: author must implement compute_bonus")


class LinUCB:
    """Per-arm LinUCB state container."""

    def __init__(self, arms: list[str], d: int, alpha: float = 1.0):
        self.arms = list(arms)
        self.d = d
        self.alpha = alpha
        self.A = {arm: np.eye(d) for arm in self.arms}
        self.b = {arm: np.zeros(d) for arm in self.arms}

    def select_arm(self, context_vec: np.ndarray) -> str:
        """Choose the arm with the highest LinUCB score."""
        raise NotImplementedError("Hard gate: author must implement select_arm")

    def update(self, arm: str, context_vec: np.ndarray, reward: float) -> None:
        """Update state for one chosen arm after observing reward."""
        raise NotImplementedError("Hard gate: author must implement update")
