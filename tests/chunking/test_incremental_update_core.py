import types
import unittest
from unittest.mock import Mock, patch

from scripts import incremental_update


class _FakeEmbedding:
    def tolist(self):
        return [0.1, 0.2, 0.3]


class _FakeSentenceTransformer:
    def __init__(self, _model_path):
        pass

    def encode(self, _text):
        return _FakeEmbedding()


class TestIncrementalUpdateCore(unittest.TestCase):
    def test_get_existing_ids_returns_empty_set_on_error(self):
        collection = Mock()
        collection.get.side_effect = RuntimeError("db down")
        self.assertEqual(incremental_update.get_existing_ids(collection), set())

    def test_get_existing_ids_returns_id_set(self):
        collection = Mock()
        collection.get.return_value = {"ids": ["a", "b", "b"]}
        self.assertEqual(incremental_update.get_existing_ids(collection), {"a", "b"})

    def test_get_chunk_id_uses_full_sha256_digest(self):
        chunk = {
            "content": "hello world",
            "metadata": {"filename": "a.md", "chunk_id": 1},
        }
        chunk_id = incremental_update.get_chunk_id(chunk)
        digest = chunk_id.rsplit("_", 1)[-1]
        self.assertRegex(digest, r"^[0-9a-f]{64}$")

    def test_index_chunks_incremental_skips_existing_ids(self):
        c1 = {
            "content": "chunk one",
            "metadata": {"filename": "a.md", "filepath": "/a.md", "chunk_id": 0, "chunk_type": "p"},
        }
        c2 = {
            "content": "chunk two",
            "metadata": {"filename": "a.md", "filepath": "/a.md", "chunk_id": 1, "chunk_type": "p"},
        }
        chunks = [c1, c2]
        existing_ids = {incremental_update.get_chunk_id(c1)}

        collection = Mock()
        collection.count.return_value = 2

        fake_sentence_transformers = types.SimpleNamespace(
            SentenceTransformer=_FakeSentenceTransformer
        )

        with patch.dict("sys.modules", {"sentence_transformers": fake_sentence_transformers}):
            with patch("scripts.incremental_update.get_local_model_path", return_value="local-model"):
                with patch(
                    "scripts.incremental_update.get_or_create_collection",
                    return_value=(object(), collection),
                ):
                    with patch(
                        "scripts.incremental_update.get_existing_ids",
                        return_value=existing_ids,
                    ):
                        incremental_update.index_chunks_incremental(
                            chunks, db_path="./tmp-vector-db"
                        )

        self.assertEqual(collection.add.call_count, 1)
        _, kwargs = collection.add.call_args
        self.assertEqual(kwargs["ids"], [incremental_update.get_chunk_id(c2)])
        self.assertEqual(kwargs["documents"], [c2["content"]])


if __name__ == "__main__":
    unittest.main()
