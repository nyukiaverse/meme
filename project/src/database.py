import sqlite3
from contextlib import contextmanager
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@contextmanager
def get_db():
    """Database connection context manager"""
    conn = sqlite3.connect('bot_data.db')
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize database tables"""
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS meme_history (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                slogan TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id INTEGER PRIMARY KEY,
                total_memes INTEGER DEFAULT 0,
                successful_generations INTEGER DEFAULT 0,
                failed_generations INTEGER DEFAULT 0,
                last_used DATETIME
            )
        ''')
        conn.commit()

def log_meme_generation(user_id: int, slogan: str, success: bool):
    """Log meme generation attempt to database"""
    try:
        with get_db() as conn:
            # Update meme history
            conn.execute(
                'INSERT INTO meme_history (user_id, slogan, timestamp) VALUES (?, ?, ?)',
                (user_id, slogan, datetime.now())
            )
            
            # Update user stats
            conn.execute('''
                INSERT INTO user_stats (user_id, total_memes, successful_generations, 
                    failed_generations, last_used)
                VALUES (?, 1, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    total_memes = total_memes + 1,
                    successful_generations = successful_generations + ?,
                    failed_generations = failed_generations + ?,
                    last_used = ?
            ''', (user_id, 1 if success else 0, 0 if success else 1, datetime.now(),
                  1 if success else 0, 0 if success else 1, datetime.now()))
            conn.commit()
    except Exception as e:
        logger.error(f"Database error: {e}") 