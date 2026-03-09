import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "circadian_tracker.db"


class DBManager:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._connect()
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                log_date TEXT NOT NULL,
                diet_pref TEXT NOT NULL,
                walk_duration INTEGER NOT NULL,
                activity TEXT NOT NULL,
                fatigue INTEGER NOT NULL,
                nap_duration INTEGER NOT NULL,
                sunlight INTEGER NOT NULL,
                breakfast TEXT,
                lunch TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS food_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                log_date TEXT NOT NULL,
                recommended_dinner TEXT NOT NULL,
                calories REAL,
                protein REAL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sleep_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                log_date TEXT NOT NULL,
                recommended_sleep_time TEXT NOT NULL,
                recommended_wake_time TEXT NOT NULL,
                chronotype TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                log_date TEXT NOT NULL,
                health_score REAL NOT NULL,
                alignment_score REAL NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        conn.commit()
        conn.close()

    def create_user(self, username: str, password_hash: str, created_at: str) -> bool:
        conn = self._connect()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, password_hash, created_at),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_user(self, username: str) -> Optional[Dict]:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def save_daily_bundle(
        self,
        user_id: int,
        daily: Dict,
        dinner: Dict,
        sleep: Dict,
        score: Dict,
    ) -> None:
        conn = self._connect()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO daily_logs (
                user_id, log_date, diet_pref, walk_duration, activity, fatigue, nap_duration,
                sunlight, breakfast, lunch, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                daily["log_date"],
                daily["diet_pref"],
                daily["walk_duration"],
                daily["activity"],
                daily["fatigue"],
                daily["nap_duration"],
                daily["sunlight"],
                daily.get("breakfast", ""),
                daily.get("lunch", ""),
                daily["created_at"],
            ),
        )

        cur.execute(
            """
            INSERT INTO food_logs (user_id, log_date, recommended_dinner, calories, protein)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                daily["log_date"],
                dinner["meal_name"],
                dinner.get("calories", 0),
                dinner.get("protein", 0),
            ),
        )

        cur.execute(
            """
            INSERT INTO sleep_logs (user_id, log_date, recommended_sleep_time, recommended_wake_time, chronotype)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                daily["log_date"],
                sleep["sleep_time"],
                sleep["wake_time"],
                sleep["chronotype"],
            ),
        )

        cur.execute(
            """
            INSERT INTO scores (user_id, log_date, health_score, alignment_score, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                daily["log_date"],
                score["health_score"],
                score["alignment_score"],
                score["status"],
            ),
        )

        conn.commit()
        conn.close()

    def get_user_history(self, user_id: int, days: int = 60) -> List[Dict]:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT d.log_date, d.walk_duration, d.activity, d.fatigue, d.nap_duration, d.sunlight,
                   s.health_score, s.alignment_score, s.status,
                   f.calories AS dinner_calories, f.protein AS dinner_protein
            FROM daily_logs d
            LEFT JOIN scores s ON s.user_id = d.user_id AND s.log_date = d.log_date
            LEFT JOIN food_logs f ON f.user_id = d.user_id AND f.log_date = d.log_date
            WHERE d.user_id = ?
            ORDER BY d.log_date DESC
            LIMIT ?
            """,
            (user_id, days),
        )
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
