"""Regression tests for RAG database path and write-safety guards.

Run from the repository root:
    python -m unittest 04-知识底座.rag.test_db_safety
"""
import importlib
import sqlite3
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

RAG_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(RAG_DIR))

try:
    import sqlite_vec  # noqa: F401
except ImportError:
    # The safety tests do not exercise vector search; stub only the extension loader.
    sys.modules["sqlite_vec"] = types.SimpleNamespace(load=lambda conn: None)

import rag


class DatabaseSafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "nested" / "test.db"
        self.db.parent.mkdir(parents=True)

    def test_missing_database_is_not_created_by_default(self):
        with patch.object(rag.sqlite_vec, "load", lambda conn: None):
            with self.assertRaises(SystemExit):
                rag.connect(self.db)
        self.assertFalse(self.db.exists())

    def test_create_requires_explicit_allow_create(self):
        with patch.object(rag.sqlite_vec, "load", lambda conn: None):
            with self.assertRaises(SystemExit):
                rag.connect(self.db, create=True)
        self.assertFalse(self.db.exists())

    def test_readonly_connection_rejects_writes(self):
        raw = sqlite3.connect(self.db)
        raw.execute("CREATE TABLE sample (value TEXT)")
        raw.commit()
        raw.close()

        with patch.object(rag.sqlite_vec, "load", lambda conn: None):
            conn = rag.connect(self.db, readonly=True)
        self.addCleanup(conn.close)
        with self.assertRaises(sqlite3.OperationalError):
            conn.execute("CREATE TABLE forbidden (value TEXT)")

    def test_rebuild_without_confirmation_preserves_database(self):
        self.db.write_bytes(b"do-not-delete")
        args = types.SimpleNamespace(confirm_rebuild=False)
        with patch.object(rag, "DB_PATH", self.db), patch.object(rag, "check_embedder") as check:
            with self.assertRaises(SystemExit):
                rag.cmd_rebuild(args)
            check.assert_not_called()
        self.assertEqual(self.db.read_bytes(), b"do-not-delete")


if __name__ == "__main__":
    unittest.main()
