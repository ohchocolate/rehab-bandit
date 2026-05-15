import numpy as np
import pytest

from bandit.linucb import (
    LinUCB,
    compute_bonus,
    compute_theta,
    predict_mean,
)


def test_initial_state_shapes():
    model = LinUCB(arms=["a", "b", "c"], d=4, alpha=0.7)

    assert model.arms == ["a", "b", "c"]
    assert model.d == 4
    assert model.alpha == 0.7

    for arm in model.arms:
        assert np.array_equal(model.A[arm], np.eye(4))
        assert np.array_equal(model.b[arm], np.zeros(4))


def test_compute_theta_is_hard_gate():
    with pytest.raises(NotImplementedError, match="compute_theta"):
        compute_theta(np.eye(2), np.zeros(2))


def test_predict_mean_is_hard_gate():
    with pytest.raises(NotImplementedError, match="predict_mean"):
        predict_mean(np.ones(2), np.ones(2))


def test_compute_bonus_is_hard_gate():
    with pytest.raises(NotImplementedError, match="compute_bonus"):
        compute_bonus(np.eye(2), np.ones(2), alpha=1.0)


def test_select_arm_is_hard_gate():
    model = LinUCB(arms=["a", "b"], d=3)

    with pytest.raises(NotImplementedError, match="select_arm"):
        model.select_arm(np.ones(3))


def test_update_is_hard_gate():
    model = LinUCB(arms=["a", "b"], d=3)

    with pytest.raises(NotImplementedError, match="update"):
        model.update("a", np.ones(3), reward=1.0)
