from bandit.arms import ARMS, ARM_IDS, get_arm


def test_six_arms_defined():
    assert len(ARMS) == 6


def test_arm_ids_unique():
    assert len(ARM_IDS) == len(set(ARM_IDS))


def test_expected_arm_ids_present():
    expected = {"upper_ankle", "lower_ankle", "stretch_ankle",
                "travel_minimal", "ankle_only", "rest"}
    assert set(ARM_IDS) == expected


def test_get_arm_returns_metadata():
    arm = get_arm("lower_ankle")
    assert arm["id"] == "lower_ankle"
    assert "description" in arm
