"""
Tests for the scheming files in the mwlr_datastore extension.

Run these tests by following the steps in local-development.md, under the Tests heading.
"""
import yaml
import os
import pytest
from pathlib import Path

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "scheming"
BASE_SCHEMA_PATH = SCHEMA_DIR / "dataset.yaml"
RESTRICTED_SCHEMA_PATH = SCHEMA_DIR / "dataset_with_restricted_resources.yaml"
DATASET_APPROVAL_SCHEMA_PATH = SCHEMA_DIR / "dataset_with_dataset_approval.yaml"
ALL_SCHEMA_PATH = SCHEMA_DIR / "dataset_with_both_restricted_resources_and_dataset_approval.yaml"

# Field names expected to exist ONLY in the additional plugins.
# Update this whenever you intentionally add/remove fields.
RESTRICTED_ONLY_FIELDS = {"resource_access_level"}
DATASET_APPROVAL_ONLY_FIELDS = {"publishing_status", "intellectual_property_review_notes", "intellectual_property_review_required", "ethics_security_risk_review_notes", "ethics_security_risk_review_required", "scientific_technical_review_required", "scientific_technical_review_notes", "te_ao_māori_review_required","te_ao_māori_review_notes", "conditions_of_release","chosen_visibility"}

# names of the scheming files to be tested.
SCHEMING_FILES = {
  "base_schema": {"path": BASE_SCHEMA_PATH, "dataset_fields": set(), "resource_fields": set()},
  "restricted_schema": {"path": RESTRICTED_SCHEMA_PATH, "dataset_fields": set(), "resource_fields": RESTRICTED_ONLY_FIELDS},
  "dataset_approval_schema": {"path": DATASET_APPROVAL_SCHEMA_PATH, "dataset_fields": DATASET_APPROVAL_ONLY_FIELDS, "resource_fields": set()},
  "all_plugins_schema": {"path": ALL_SCHEMA_PATH, "dataset_fields": DATASET_APPROVAL_ONLY_FIELDS, "resource_fields": RESTRICTED_ONLY_FIELDS}, # additional fields from all plugins
}

NON_BASE_SCHEMA_NAMES = [key for key in SCHEMING_FILES if key != "base_schema"]
FIELD_LIST_KEYS = ["dataset_fields", "resource_fields"]

@pytest.mark.parametrize("schema_key", list(SCHEMING_FILES.keys())) # run this test for all schema files
def test_scheming_files_exist(schema_key):
    """
    Test that the scheming files exist in the mwlr_datastore extension.
    """
    file_path = SCHEMING_FILES[schema_key]["path"]
    assert os.path.exists(file_path), f"{file_path} does not exist"

@pytest.mark.parametrize("field_list_key", FIELD_LIST_KEYS)
@pytest.mark.parametrize("schema_key", NON_BASE_SCHEMA_NAMES) # run this test for all non-base schema files
def test_additional_fields_are_as_expected(schema_key, field_list_key):

    """Assert that the fields in the additional scheming file are as expected compared to the base scheming file."""

    base = _load_schema(SCHEMING_FILES["base_schema"]["path"])
    plugin_schema = _load_schema(SCHEMING_FILES[schema_key]["path"])
    expected = SCHEMING_FILES[schema_key][field_list_key]

    base_names = set(_fields_by_name(base.get(field_list_key, [])))
    plugin_names = set(_fields_by_name(plugin_schema.get(field_list_key, [])))
    additional = plugin_names - base_names

    assert additional == expected, (
        f"[{schema_key}.{field_list_key}] "
        f"missing={sorted(expected - additional)} "
        f"unexpected={sorted(additional - expected)}"
    )

def _load_schema(path):
    with open(path) as f:
        return yaml.safe_load(f)

def _fields_by_name(field_list):
    """Key a dataset_fields/resource_fields list by field_name so comparisons
    don't care about ordering."""
    return {field["field_name"]: field for field in field_list}

@pytest.mark.parametrize("field_list_key", FIELD_LIST_KEYS)
@pytest.mark.parametrize("schema_key", NON_BASE_SCHEMA_NAMES)
def test_base_fields_present_in_every_schema(schema_key, field_list_key):
    """No schema file should ever drop a base field."""
    base = _load_schema(SCHEMING_FILES["base_schema"]["path"])
    plugin_schema = _load_schema(SCHEMING_FILES[schema_key]["path"])

    base_names = set(_fields_by_name(base.get(field_list_key, [])))
    plugin_names = set(_fields_by_name(plugin_schema.get(field_list_key, [])))

    missing = base_names - plugin_names
    assert not missing, f"[{schema_key}.{field_list_key}] missing base field(s): {sorted(missing)}"


@pytest.mark.parametrize("field_list_key", FIELD_LIST_KEYS)
def test_shared_fields_identical_across_all_files(field_list_key):
    """Any field appearing in more than one schema file must
    be defined identically everywhere."""
    schemas = {key: _load_schema(info["path"]) for key, info in SCHEMING_FILES.items()}

    seen = {}
    for schema_key, schema in schemas.items():
        for field in schema.get(field_list_key, []):
            seen.setdefault(field["field_name"], {})[schema_key] = field

    problems = []
    for field_name, defs_by_schema in seen.items():
        reference_key, reference_def = next(iter(defs_by_schema.items()))
        for schema_key, field_def in defs_by_schema.items():
            if field_def != reference_def:
                problems.append(f"'{field_name}' differs between {reference_key} and {schema_key}")

    assert not problems, f"[{field_list_key}] " + "; ".join(problems)


@pytest.mark.parametrize("schema_key", NON_BASE_SCHEMA_NAMES)
def test_other_schema_keys_match_base(schema_key):
    """Everything outside dataset_fields/resource_fields (scheming_version,
    dataset_type, about, etc.) should be identical to the base schema."""
    ignored = set(FIELD_LIST_KEYS)
    base = _load_schema(SCHEMING_FILES["base_schema"]["path"])
    plugin_schema = _load_schema(SCHEMING_FILES[schema_key]["path"])

    base_rest = {k: v for k, v in base.items() if k not in ignored}
    plugin_rest = {k: v for k, v in plugin_schema.items() if k not in ignored}

    assert base_rest == plugin_rest, f"[{schema_key}] non-field keys differ from base schema"