import sqlite3
from pathlib import Path

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def connect(path=":memory:"):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn, with_indexes=True):
    """Create schema, triggers, views and (optionally) secondary indexes."""
    files = ["01_schema.sql", "02_triggers.sql", "03_views.sql"]
    if with_indexes:
        files.append("04_indexes.sql")
    for name in files:
        conn.executescript((SQL_DIR / name).read_text())
    conn.commit()


def add_indexes(conn):
    conn.executescript((SQL_DIR / "04_indexes.sql").read_text())
    conn.commit()


def analytics_queries():
    """Parse 05_analytics.sql into {name: sql}."""
    out, name, buf = {}, None, []
    for line in (SQL_DIR / "05_analytics.sql").read_text().splitlines():
        if line.startswith("-- name:"):
            if name:
                out[name] = "\n".join(buf).strip().rstrip(";")
            name, buf = line.split(":", 1)[1].strip(), []
        else:
            buf.append(line)
    if name:
        out[name] = "\n".join(buf).strip().rstrip(";")
    return out
