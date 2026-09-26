"""Reproductibilité des expériences ML."""

from __future__ import annotations

import os
import random

import numpy as np


def reset_random_seeds(seed: int = 42) -> None:
    """Fixe les graines aléatoires pour Python, NumPy et TensorFlow."""
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)

    try:
        import tensorflow as tf

        tf.random.set_seed(seed)
    except ImportError:
        pass
