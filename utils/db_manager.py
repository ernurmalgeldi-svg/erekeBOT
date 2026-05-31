import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import os
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

class DBManager:
    def get_connection(self):
        try:
            conn = psycopg2.connect(
                user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT, database=DB_NAME,
                options="-c client_encoding=UTF8"
            )
            # БАЗАНЫ ТОЛЫҚТАЙ БРОНЬДАУ (БАРЛЫҚ ID-ДІ BIGINT-ҚА КҮШТЕП ӨЗГЕРТУ)
            with conn.cursor() as cur:
                cur.execute("ALTER TABLE messages ALTER COLUMN user_id TYPE BIGINT;")
                # Егер rate_limits кестесінде де қолданушы ID-і болса, оны да түзетеміз
                try:
                    cur.execute("ALTER TABLE rate_limits ALTER COLUMN key TYPE TEXT;")
                except Exception:
                    pass
                conn.commit()
            return conn
        except Exception:
            return None

    async def check_rate_limit(self, key: str, capacity: int, refill_rate: float) -> bool:
        conn = self.get_connection()
        if not conn: return True
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO rate_limits (key, tokens, last_update) VALUES (%s, %s - 1, NOW())
                    ON CONFLICT (key) DO UPDATE
                    SET tokens = LEAST(%s::float, rate_limits.tokens + EXTRACT(EPOCH FROM (NOW() - rate_limits.last_update)) * %s) - 1, last_update = NOW()
                    RETURNING tokens;
                """, (str(key), capacity, capacity, refill_rate))
                row = cursor.fetchone()
                conn.commit()
                return row[0] >= 0 if row else True
        except Exception: return True
        finally: conn.close()

    async def get_chat_history(self, user_id: int, limit: int = 10) -> list:
        conn = self.get_connection()
        if not conn: return []
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Осы жерде де BIGINT формат сақталады
                cursor.execute("SELECT user_message, bot_response FROM messages WHERE user_id = %s ORDER BY created_at DESC LIMIT %s", (int(user_id), limit))
                rows = cursor.fetchall()
            history = []
            for row in reversed(rows):
                if row['user_message']: history.append({"role": "user", "content": str(row['user_message'])})
                if row['bot_response']: history.append({"role": "assistant", "content": str(row['bot_response'])})
            return history
        except Exception: return []
        finally: conn.close()

    async def save_message(self, user_id: int, user_message: str, bot_response: str):
        conn = self.get_connection()
        if not conn: return
        try:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO messages (user_id, user_message, bot_response) VALUES (%s, %s, %s)", (int(user_id), str(user_message), str(bot_response)))
                conn.commit()
                logging.info(f"💾 Базаға сәтті жазылды!")
        except Exception as e: 
            logging.error(f"Жазу қатесі: {e}")
        finally: conn.close()

    async def replace_history_with_summary(self, user_id: int, summary: str):
        conn = self.get_connection()
        if not conn: return
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM messages WHERE user_id = %s", (int(user_id),))
                cursor.execute("INSERT INTO messages (user_id, user_message, bot_response) VALUES (%s, %s, %s)", (int(user_id), "[СИСТЕМА: СУММАРИЗАЦИЯ]", str(summary)))
                conn.commit()
        except Exception: pass
        finally: conn.close()

db = DBManager()