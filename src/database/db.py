import sqlite3
import logging
from pathlib import Path
from src.config import DATABASE_PATH

logger = logging.getLogger("db")

def get_connection(db_path: Path = DATABASE_PATH) -> sqlite3.Connection:
    """Creates a sqlite3 database connection."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=15)
    conn.row_factory = sqlite3.Row
    # SQLite does not enforce foreign keys (and therefore ON DELETE CASCADE) unless asked to.
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db(db_path: Path = DATABASE_PATH) -> None:
    """Initializes SQLite database tables with parameterized DDL."""
    conn = None
    try:
        conn = get_connection(db_path)
        with conn:
            # Table: analyses
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, crop TEXT NOT NULL, input_mode TEXT NOT NULL,
                    symptoms TEXT, has_image INTEGER DEFAULT 0, result_condition TEXT NOT NULL, confidence REAL DEFAULT 0.0,
                    evidence_level TEXT DEFAULT 'Insufficient evidence', severity TEXT NOT NULL, report_json TEXT,
                    plant_id INTEGER, environment_json TEXT DEFAULT '{}', model_version TEXT DEFAULT 'heuristic-v1',
                    knowledge_version TEXT DEFAULT 'local-kb', created_at TEXT NOT NULL
                );
            """)


            conn.execute("""CREATE TABLE IF NOT EXISTS plants (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, crop TEXT NOT NULL, variety TEXT,
                planting_date TEXT, location TEXT, growing_environment TEXT, notes TEXT, created_at TEXT NOT NULL
            );""")
            conn.execute("""CREATE TABLE IF NOT EXISTS analysis_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT, analysis_id INTEGER NOT NULL, image_index INTEGER NOT NULL,
                filename TEXT, width INTEGER, height INTEGER, quality TEXT, sharpness REAL, brightness REAL,
                FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
            );""")
            conn.execute("""CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT, plant_id INTEGER NOT NULL, due_date TEXT NOT NULL,
                note TEXT NOT NULL, completed INTEGER DEFAULT 0, FOREIGN KEY (plant_id) REFERENCES plants(id) ON DELETE CASCADE
            );""")

            # Table: messages
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id INTEGER,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (analysis_id) REFERENCES analyses (id) ON DELETE CASCADE
                );
            """)

            # Table: settings (persistent user preferences, JSON-encoded values)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # Table: evidence
            conn.execute("""
                CREATE TABLE IF NOT EXISTS evidence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id INTEGER,
                    source TEXT,
                    title TEXT,
                    content TEXT,
                    url TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (analysis_id) REFERENCES analyses (id) ON DELETE CASCADE
                );
            """)
        # Lightweight migration for databases created by older versions.
        existing = {row[1] for row in conn.execute("PRAGMA table_info(analyses)").fetchall()}
        migrations = {
            "evidence_level": "ALTER TABLE analyses ADD COLUMN evidence_level TEXT DEFAULT 'Insufficient evidence'",
            "plant_id": "ALTER TABLE analyses ADD COLUMN plant_id INTEGER",
            "environment_json": "ALTER TABLE analyses ADD COLUMN environment_json TEXT DEFAULT '{}'",
            "model_version": "ALTER TABLE analyses ADD COLUMN model_version TEXT DEFAULT 'heuristic-v1'",
            "knowledge_version": "ALTER TABLE analyses ADD COLUMN knowledge_version TEXT DEFAULT 'local-kb'",
        }
        for col, ddl in migrations.items():
            if col not in existing:
                conn.execute(ddl)
        conn.commit()
        logger.info(f"Database initialized successfully at {db_path}")
    except Exception as e:
        logger.error(f"Error initializing SQLite database: {e}")
        raise e
    finally:
        if conn is not None:
            conn.close()
