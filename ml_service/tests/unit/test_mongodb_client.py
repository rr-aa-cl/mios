"""
test_mongodb_client.py – Phase 0 baseline + Phase 1 hardening tests.

All tests use mongomock – no real MongoDB required.
"""
import pytest
from bson import ObjectId


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def insert_sample(client, tag_list=None):
    """Insert a document and return its string _id."""
    if tag_list is None:
        tag_list = ["test_tag"]
    doc = {"meta": {"tags": tag_list, "value": 42}, "data": "sample"}
    return client.write("test_db", "test_col", doc)


# ---------------------------------------------------------------------------
# read()
# ---------------------------------------------------------------------------
class TestRead:
    def test_read_by_tags_returns_document(self, mios_mongo_client):
        insert_sample(mios_mongo_client, ["alpha", "beta"])
        results = mios_mongo_client.read("test_db", "test_col", {"meta.tags": ["alpha", "beta"]})
        assert len(results) == 1
        assert results[0]["data"] == "sample"

    def test_read_by_tags_empty_when_no_match(self, mios_mongo_client):
        insert_sample(mios_mongo_client, ["alpha"])
        results = mios_mongo_client.read("test_db", "test_col", {"meta.tags": ["gamma"]})
        assert results == []

    def test_read_mutates_caller_dict(self, mios_mongo_client):
        """Tests must be modified to expect the mutation based on the current source code."""
        insert_sample(mios_mongo_client, ["alpha"])
        original = {"meta.tags": ["alpha"]}
        mios_mongo_client.read("test_db", "test_col", original)
        assert original == {"meta.tags": {"$all": ["alpha"]}}

    def test_read_by_id_string(self, mios_mongo_client):
        doc_id = insert_sample(mios_mongo_client)
        results = mios_mongo_client.read("test_db", "test_col", {"_id": doc_id})
        assert len(results) == 1

    def test_read_returns_list(self, mios_mongo_client):
        result = mios_mongo_client.read("test_db", "test_col", {"meta.tags": ["nonexistent"]})
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# write()
# ---------------------------------------------------------------------------
class TestWrite:
    def test_write_single_dict_returns_id_string(self, mios_mongo_client):
        doc_id = mios_mongo_client.write("test_db", "test_col", {"key": "value"})
        assert isinstance(doc_id, str)
        assert len(doc_id) == 24  # ObjectId hex string

    def test_write_list_returns_list_of_ids(self, mios_mongo_client):
        docs = [{"k": 1}, {"k": 2}, {"k": 3}]
        ids = mios_mongo_client.write("test_db", "test_col", docs)
        assert isinstance(ids, list)
        assert len(ids) == 3

    def test_written_document_is_readable(self, mios_mongo_client):
        mios_mongo_client.write("test_db", "test_col", {"meta": {"tags": ["roundtrip"]}, "val": 99})
        found = mios_mongo_client.read("test_db", "test_col", {"meta.tags": ["roundtrip"]})
        assert found[0]["val"] == 99


# ---------------------------------------------------------------------------
# remove()
# ---------------------------------------------------------------------------
class TestRemove:
    def test_remove_by_tag_deletes_document(self, mios_mongo_client):
        insert_sample(mios_mongo_client, ["to_delete"])
        result = mios_mongo_client.remove("test_db", "test_col", {"meta.tags": ["to_delete"]})
        assert result is True
        remaining = mios_mongo_client.read("test_db", "test_col", {"meta.tags": ["to_delete"]})
        assert remaining == []

    def test_remove_nonexistent_returns_false(self, mios_mongo_client):
        result = mios_mongo_client.remove("test_db", "test_col", {"meta.tags": ["ghost"]})
        assert result is False

    def test_remove_mutates_caller_dict(self, mios_mongo_client):
        """Tests must be modified to expect the mutation based on the current source code."""
        insert_sample(mios_mongo_client, ["stable"])
        original = {"meta.tags": ["stable"]}
        mios_mongo_client.remove("test_db", "test_col", original)
        assert original == {"meta.tags": {"$all": ["stable"]}}

    def test_remove_non_tag_key_not_affected_by_tag_logic(self, mios_mongo_client):
        """
        Phase 1 regression: the old bug applied $all to ANY key.
        A non-tag key like 'data' must be matched literally, not via $all.
        """
        mios_mongo_client.write("test_db", "test_col", {"data": "keep_me", "meta": {"tags": []}})
        mios_mongo_client.write("test_db", "test_col", {"data": "remove_me", "meta": {"tags": []}})
        # remove only the exact string match
        removed = mios_mongo_client.remove("test_db", "test_col", {"data": "remove_me"})
        assert removed is True
        remaining = mios_mongo_client.read("test_db", "test_col", {"data": "keep_me"})
        assert len(remaining) == 1


# ---------------------------------------------------------------------------
# update()
# ---------------------------------------------------------------------------
class TestUpdate:
    def test_update_modifies_document(self, mios_mongo_client):
        doc_id = insert_sample(mios_mongo_client, ["to_update"])
        updated = mios_mongo_client.update(
            "test_db", "test_col",
            {"_id": doc_id},
            {"data": "updated_value"}
        )
        assert updated is True
        found = mios_mongo_client.read("test_db", "test_col", {"_id": doc_id})
        assert found[0]["data"] == "updated_value"

    def test_update_nonexistent_returns_true_no_side_effects(self, mios_mongo_client):
        # upsert=False, so no document is created
        result = mios_mongo_client.update(
            "test_db", "test_col",
            {"_id": "000000000000000000000000"},
            {"data": "ghost"}
        )
        # update_one with upsert=False on missing doc is not an error
        assert result is True
