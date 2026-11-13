"""Regression tests for coordinator-backed entity subscriptions."""

import ast
from pathlib import Path

INTEGRATION = Path(__file__).parents[1] / "custom_components" / "idaho_falls_snow"


def _class_bases(path, class_name):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                base.id if isinstance(base, ast.Name) else ast.unparse(base)
                for base in node.bases
            }
    raise AssertionError(f"Class {class_name} was not found in {path.name}")


def test_regular_sensors_subscribe_to_coordinator_updates():
    bases = _class_bases(INTEGRATION / "sensor.py", "BaseSnowSensor")
    assert "CoordinatorEntity" in bases
    assert "SensorEntity" in bases


def test_snow_event_binary_sensor_subscribes_to_coordinator_updates():
    bases = _class_bases(INTEGRATION / "binary_sensor.py", "SnowEvent")
    assert "CoordinatorEntity" in bases
    assert "BinarySensorEntity" in bases
