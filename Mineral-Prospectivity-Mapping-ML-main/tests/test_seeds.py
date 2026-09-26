"""Tests de reproductibilité."""

from compass_core.utils.seeds import reset_random_seeds


def test_reset_seeds_idempotent() -> None:
    reset_random_seeds(123)
    reset_random_seeds(123)
