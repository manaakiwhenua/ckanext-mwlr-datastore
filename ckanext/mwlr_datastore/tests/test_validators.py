"""Tests for logic/validators.py.

These cover the pure validators only - no database, no app fixtures - so they
run wherever CKAN is importable.
"""
import pytest

from ckan.plugins.toolkit import Invalid

from ckanext.mwlr_datastore.logic import validators


@pytest.mark.parametrize("value", [None, "", "   "])
def test_is_number_treats_blank_as_absent(value):
    assert validators.is_number(value) is None


@pytest.mark.parametrize("value", ["3.5", "-2", "1e3", "0"])
def test_is_number_accepts_numbers(value):
    assert validators.is_number(value) == value


def test_is_number_rejects_non_numbers():
    with pytest.raises(Invalid):
        validators.is_number("abc")


@pytest.mark.parametrize("value", [None, "", "   "])
def test_is_elevation_range_treats_blank_as_absent(value):
    assert validators.is_elevation_range(value) is None


@pytest.mark.parametrize("value", ["-19", "0", "100", "2999"])
def test_is_elevation_range_accepts_values_inside_the_range(value):
    assert validators.is_elevation_range(value) == value


# The bounds are exclusive: the implementation tests -20 < r < 3000, so the
# endpoints named in its own error message are themselves rejected.
@pytest.mark.parametrize("value", ["-20", "-21", "3000", "3001", "abc"])
def test_is_elevation_range_rejects_values_outside_the_range(value):
    with pytest.raises(Invalid):
        validators.is_elevation_range(value)


def test_is_year_accepts_a_bare_year():
    assert validators.is_year("2015") == "2015"


@pytest.mark.parametrize("value", ["2015-01", "2015-01-29", "nope"])
def test_is_year_rejects_anything_else(value):
    with pytest.raises(Invalid):
        validators.is_year(value)


def test_is_year_month_accepts_year_month():
    assert validators.is_year_month("2015-01") == "2015-01"


@pytest.mark.parametrize("value", ["2015", "2015-01-29", "nope"])
def test_is_year_month_rejects_anything_else(value):
    with pytest.raises(Invalid):
        validators.is_year_month(value)


def test_is_year_month_day_accepts_a_full_date():
    assert validators.is_year_month_day("2015-01-29") == "2015-01-29"


@pytest.mark.parametrize("value", ["2015", "2015-01", "nope"])
def test_is_year_month_day_rejects_anything_else(value):
    with pytest.raises(Invalid):
        validators.is_year_month_day(value)


@pytest.mark.parametrize("value", ["2015", "2015-01", "2015-01-29"])
def test_is_date_accepts_all_three_granularities(value):
    assert validators.is_date(value) == value


@pytest.mark.parametrize("value", ["29-01-2015", "nope"])
def test_is_date_rejects_other_formats(value):
    with pytest.raises(Invalid):
        validators.is_date(value)


@pytest.mark.parametrize(
    "before,after",
    [(".csv", "csv"), ("csv", "csv"), (".", "."), ("", ""), (5, 5)],
)
def test_remove_leading_dot_if_present(before, after):
    key = ("format",)
    data = {key: before}
    validators.remove_leading_dot_if_present(key, data, {}, {})
    assert data[key] == after


def test_convert_custom_fields_drops_wholly_empty_pairs():
    data = {
        ("custom", 0, "custom_key"): "",
        ("custom", 0, "custom_value"): "",
        ("custom", 1, "custom_key"): "depth",
        ("custom", 1, "custom_value"): "10m",
    }
    validators.convert_custom_fields(None, data, {}, {})
    assert set(data) == {
        ("custom", 1, "custom_key"),
        ("custom", 1, "custom_value"),
    }


def test_bounding_box_surrounds_the_point():
    lat, lon = -41.29, 174.78
    lat_min, lon_min, lat_max, lon_max = validators.boundingBox(lat, lon, 0.025, 0.025)
    assert lat_min < lat < lat_max
    assert lon_min < lon < lon_max


def test_get_validators_exposes_every_public_validator():
    registered = validators.get_validators()
    assert set(registered) == {
        "ckanext_mwlr_datastore_is_year",
        "ckanext_mwlr_datastore_is_date",
        "ckanext_mwlr_datastore_is_number",
        "ckanext_mwlr_datastore_is_elevation_range",
        "ckanext_mwlr_datastore_convert_spatial",
        "ckanext_mwlr_datastore_convert_custom_fields",
        "ckanext_mwlr_datastore_remove_leading_dot_if_present",
    }
