"""Regression tests for GIS status and City page parsing."""

from custom_components.idaho_falls_snow.parsing import (
    completed,
    updated_date,
    working,
    zone_key,
)


def test_working_statuses_are_recognized_without_substring_false_positives():
    assert working("Working")
    assert working("In Progress")
    assert working("ACTIVE")
    assert working("Plowing - Priority 1")
    assert not working("Inactive")
    assert not working("Not active")
    assert not working("Started later")


def test_completed_statuses_are_recognized_without_substring_false_positives():
    assert completed("Complete")
    assert completed("Completed")
    assert completed("Finished")
    assert completed("Done")
    assert completed("Plowed")
    assert not completed("Incomplete")
    assert not completed("Not completed")
    assert not completed("Undone")


def test_city_page_updated_date_accepts_abbreviated_months():
    assert updated_date("Page details. Updated Feb. 20, 2025. More text.") == "Feb. 20, 2025"
    assert updated_date("Updated February 20, 2025") == "February 20, 2025"
    assert updated_date("No update date here") is None


def test_zone_key_normalizes_known_zone_names():
    assert zone_key("Downtown") == "downtown"
    assert zone_key("Zone A") == "a"
    assert zone_key("ZONE B") == "b"
    assert zone_key("1") == "a"
    assert zone_key("2") == "b"
