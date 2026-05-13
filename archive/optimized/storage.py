import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Any, Generator
from dataclasses import dataclass
import threading


@dataclass
class DBConfig:
    db_path: str = "./data/index.db"
    wal_mode: bool = True
    cache_size: int = 10000
    mmap_size: int = 268435456


class SQLiteStorage:
    def __init__(self, config: DBConfig = None):
        self.config = config or DBConfig()
        self.db_path = Path(self.config.db_path)
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            with self._lock:
                if self._conn is None:
                    self.db_path.parent.mkdir(parents=True, exist_ok=True)
                    self._conn = sqlite3.connect(
                        str(self.db_path),
                        check_same_thread=False
                    )
                    self._conn.execute(f"PRAGMA cache_size = {self.config.cache_size}")
                    self._conn.execute("PRAGMA temp_store = MEMORY")
                    if self.config.wal_mode:
                        self._conn.execute("PRAGMA journal_mode = WAL")
                        self._conn.execute("PRAGMA synchronous = NORMAL")
                    self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self):
        conn = self._get_connection()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chunk_id TEXT UNIQUE NOT NULL,
                content TEXT NOT NULL,
                file_path TEXT NOT NULL,
                language TEXT,
                start_line INTEGER,
                end_line INTEGER,
                chunk_type TEXT,
                symbols TEXT,
                docstring TEXT,
                imports TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_file_path ON chunks(file_path);
            CREATE INDEX IF NOT EXISTS idx_language ON chunks(language);
            CREATE INDEX IF NOT EXISTS idx_chunk_type ON chunks(chunk_type);

            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                chunk_id,
                content,
                content='chunks',
                content_rowid='id'
            );

            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chunk_id TEXT NOT NULL,
                name TEXT NOT NULL,
                type TEXT,
                line INTEGER,
                signature TEXT,
                FOREIGN KEY (chunk_id) REFERENCES chunks(chunk_id)
            );

            CREATE INDEX IF NOT EXISTS idx_symbol_name ON symbols(name);
            CREATE INDEX IF NOT EXISTS idx_symbol_chunk ON symbols(chunk_id);
        """)

    def insert_chunks(self, chunks: List[Dict]) -> int:
        conn = self._get_connection()
        inserted = 0

        for chunk in chunks:
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO chunks
                    (chunk_id, content, file_path, language, start_line, end_line,
                     chunk_type, symbols, docstring, imports)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    chunk.get('chunk_id', ''),
                    chunk.get('content', ''),
                    chunk.get('file_path', ''),
                    chunk.get('language', ''),
                    chunk.get('start_line', 0),
                    chunk.get('end_line', 0),
                    chunk.get('chunk_type', ''),
                    json.dumps(chunk.get('symbols', [])),
                    chunk.get('docstring', ''),
                    json.dumps(chunk.get('imports', []))
                ))

                for sym in chunk.get('symbols', []):
                    conn.execute("""
                        INSERT INTO symbols (chunk_id, name, type, line, signature)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        chunk.get('chunk_id', ''),
                        sym.get('name', ''),
                        sym.get('type', ''),
                        sym.get('start', 0),
                        sym.get('signature', '')
                    ))

                inserted += 1
            except Exception as e:
                print(f"Error inserting chunk: {e}")

        conn.commit()
        return inserted

    def get_chunk(self, chunk_id: str) -> Optional[Dict]:
        conn = self._get_connection()
        row = conn.execute(
            "SELECT * FROM chunks WHERE chunk_id = ?",
            (chunk_id,)
        ).fetchone()

        if row:
            return self._row_to_dict(row)
        return None

    def get_chunks_by_file(self, file_path: str) -> List[Dict]:
        conn = self._get_connection()
        rows = conn.execute(
            "SELECT * FROM chunks WHERE file_path = ? ORDER BY start_line",
            (file_path,)
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def search_by_content(self, query: str, limit: int = 100) -> List[Dict]:
        conn = self._get_connection()
        rows = conn.execute("""
            SELECT c.* FROM chunks c
            JOIN chunks_fts fts ON c.chunk_id = fts.chunk_id
            WHERE chunks_fts MATCH ?
            LIMIT ?
        """, (query, limit)).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_symbol_chunks(self, symbol_name: str) -> List[Dict]:
        conn = self._get_connection()
        rows = conn.execute("""
            SELECT c.* FROM chunks c
            JOIN symbols s ON c.chunk_id = s.chunk_id
            WHERE s.name = ?
            GROUP BY c.chunk_id
        """, (symbol_name,)).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_stats(self) -> Dict:
        conn = self._get_connection()

        stats = {}

        stats['total_chunks'] = conn.execute(
            "SELECT COUNT(*) FROM chunks"
        ).fetchone()[0]

        stats['total_files'] = conn.execute(
            "SELECT COUNT(DISTINCT file_path) FROM chunks"
        ).fetchone()[0]

        stats['total_symbols'] = conn.execute(
            "SELECT COUNT(*) FROM symbols"
        ).fetchone()[0]

        stats['by_language'] = {}
        for row in conn.execute(
            "SELECT language, COUNT(*) as cnt FROM chunks GROUP BY language"
        ):
            stats['by_language'][row[0]] = row[1]

        stats['by_type'] = {}
        for row in conn.execute(
            "SELECT chunk_type, COUNT(*) as cnt FROM chunks GROUP BY chunk_type"
        ):
            stats['by_type'][row[0]] = row[1]

        return stats

    def set_metadata(self, key: str, value: Any):
        conn = self._get_connection()
        conn.execute("""
            INSERT OR REPLACE INTO metadata (key, value)
            VALUES (?, ?)
        """, (key, json.dumps(value)))
        conn.commit()

    def get_metadata(self, key: str) -> Any:
        conn = self._get_connection()
        row = conn.execute(
            "SELECT value FROM metadata WHERE key = ?",
            (key,)
        ).fetchone()
        if row:
            return json.loads(row[0])
        return None

    def iter_chunks(self, batch_size: int = 100) -> Generator[Dict, None, None]:
        conn = self._get_connection()
        cursor = conn.execute("SELECT * FROM chunks")
        while True:
            rows = cursor.fetchmany(batch_size)
            if not rows:
                break
            for row in rows:
                yield self._row_to_dict(row)

    def delete_all(self):
        conn = self._get_connection()
        conn.execute("DELETE FROM symbols")
        conn.execute("DELETE FROM chunks")
        conn.execute("DELETE FROM metadata")
        conn.commit()

    def vacuum(self):
        conn = self._get_connection()
        conn.execute("VACUUM")

    def get_size(self) -> int:
        return self.db_path.stat().st_size if self.db_path.exists() else 0

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def _row_to_dict(self, row) -> Dict:
        if isinstance(row, dict):
            d = dict(row)
        else:
            d = dict(zip([c[0] for c in self._get_connection().execute("PRAGMA table_info(chunks)").fetchall()], row))

        if 'symbols' in d and isinstance(d['symbols'], str):
            d['symbols'] = json.loads(d['symbols'])
        if 'imports' in d and isinstance(d['imports'], str):
            d['imports'] = json.loads(d['imports'])

        return d


class StorageFacade:
    def __init__(self, storage_path: str = "./data"):
        self.path = Path(storage_path)
        self.path.mkdir(parents=True, exist_ok=True)

        self.sqlite = SQLiteStorage(DBConfig(
            db_path=str(self.path / "index.db")
        ))

    def save_chunks(self, chunks: List[Dict]) -> int:
        return self.sqlite.insert_chunks(chunks)

    def get_chunk(self, chunk_id: str) -> Optional[Dict]:
        return self.sqlite.get_chunk(chunk_id)

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        return self.sqlite.search_by_content(query, limit)

    def get_by_file(self, file_path: str) -> List[Dict]:
        return self.sqlite.get_chunks_by_file(file_path)

    def get_by_symbol(self, symbol_name: str) -> List[Dict]:
        return self.sqlite.get_symbol_chunks(symbol_name)

    def stats(self) -> Dict:
        stats = self.sqlite.get_stats()
        stats['db_size_bytes'] = self.sqlite.get_size()
        return stats

    def clear(self):
        self.sqlite.delete_all()

    def close(self):
        self.sqlite.close()
