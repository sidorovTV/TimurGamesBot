import aiosqlite
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from app.utils.logger import db_logger

DATABASE_PATH = 'data/TGB.sqlite'


async def init_db():
    db_logger.info("Initializing database")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            # Создаем таблицу users, если она еще не существует
            await db.execute('''CREATE TABLE IF NOT EXISTS users
                                (id INTEGER PRIMARY KEY, name TEXT, age INTEGER, username TEXT, is_blocked INTEGER DEFAULT 0,
                                 block_reason TEXT)''')

            # Создаем таблицу sessions, если она еще не существует
            await db.execute('''CREATE TABLE IF NOT EXISTS sessions
                                (id INTEGER PRIMARY KEY, game TEXT, date TEXT, time TEXT, max_players INTEGER, creator_id INTEGER)''')

            # Создаем таблицу participants, если она еще не существует
            await db.execute('''CREATE TABLE IF NOT EXISTS participants
                                (session_id INTEGER, user_id INTEGER, PRIMARY KEY (session_id, user_id))''')

            # Создаем таблицу session_confirmations, если она еще не существует
            await db.execute('''CREATE TABLE IF NOT EXISTS session_confirmations
                                (session_id INTEGER, user_id INTEGER, status TEXT, 
                                 PRIMARY KEY (session_id, user_id))''')

            # Создаем новую таблицу user_session_events для хранения истории событий
            await db.execute('''CREATE TABLE IF NOT EXISTS user_session_events
                                (id INTEGER PRIMARY KEY,
                                 user_id INTEGER,
                                 session_id INTEGER,
                                 event_type TEXT,
                                 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

            await db.commit()
            db_logger.info("Database initialized successfully")
        except Exception as e:
            db_logger.error(f"Error initializing database: {e}", exc_info=True)
            raise


async def save_user(name: str, age: int, username: str, user_id: int):
    db_logger.info(f"Saving user: {user_id}, {name}")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("INSERT OR REPLACE INTO users (id, name, age, username) VALUES (?, ?, ?, ?)",
                             (user_id, name, age, username))
            await db.commit()
            db_logger.info(f"User {user_id} saved successfully")
        except Exception as e:
            db_logger.error(f"Error saving user {user_id}: {e}", exc_info=True)
            raise


async def is_user_registered(user_id: int) -> bool:
    db_logger.info(f"Checking if user {user_id} is registered")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            async with db.execute("SELECT id FROM users WHERE id = ?", (user_id,)) as cursor:
                result = await cursor.fetchone()
                is_registered = result is not None
                db_logger.info(f"User {user_id} registration status: {is_registered}")
                return is_registered
        except Exception as e:
            db_logger.error(f"Error checking user registration for {user_id}: {e}", exc_info=True)
            raise

async def create_session(game: str, date: str, time: str, max_players: int, creator_id: int) -> int:
    db_logger.info(f"Attempting to create new session. Game: {game}, Date: {date}, Time: {time}, Max Players: {max_players}, Creator ID: {creator_id}")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            cursor = await db.execute(
                "INSERT INTO sessions (game, date, time, max_players, creator_id) VALUES (?, ?, ?, ?, ?)",
                (game, date, time, max_players, creator_id))
            session_id = cursor.lastrowid
            await db.commit()
            db_logger.info(f"Session created successfully. Session ID: {session_id}")
            return session_id
        except aiosqlite.Error as e:
            db_logger.error(f"Database error while creating session: {e}", exc_info=True)
            raise
        except Exception as e:
            db_logger.error(f"Unexpected error while creating session: {e}", exc_info=True)
            raise


async def join_session(session_id: int, user_id: int):
    db_logger.info(f"Attempting to join session. Session ID: {session_id}, User ID: {user_id}")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("INSERT OR IGNORE INTO participants (session_id, user_id) VALUES (?, ?)",
                             (session_id, user_id))
            await db.commit()
            db_logger.info(f"User {user_id} successfully joined session {session_id}")
        except aiosqlite.Error as e:
            db_logger.error(f"Database error while joining session: {e}", exc_info=True)
            raise
        except Exception as e:
            db_logger.error(f"Unexpected error while joining session: {e}", exc_info=True)
            raise

async def get_sessions():
    db_logger.info("Fetching all active sessions")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT s.id, s.game, s.date, s.time, s.max_players,
                       COUNT(p.user_id) as current_players, u.name as creator_name
                FROM sessions s
                LEFT JOIN participants p ON s.id = p.session_id
                JOIN users u ON s.creator_id = u.id
                WHERE s.date >= date('now') and s.time >= time('now','localtime')
                GROUP BY s.id
                ORDER BY s.date, s.time;
            """) as cursor:
                sessions = await cursor.fetchall()
            db_logger.info(f"Retrieved {len(sessions)} active sessions")
            return sessions
        except aiosqlite.Error as e:
            db_logger.error(f"Database error while fetching sessions: {e}", exc_info=True)
            raise
        except Exception as e:
            db_logger.error(f"Unexpected error while fetching sessions: {e}", exc_info=True)
            raise

async def get_session_participants(session_id: int):
    db_logger.info(f"Fetching participants for session ID: {session_id}")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT u.id, u.name, u.username
                FROM participants p
                JOIN users u ON p.user_id = u.id
                WHERE p.session_id = ?
            """, (session_id,)) as cursor:
                participants = await cursor.fetchall()
            db_logger.info(f"Retrieved {len(participants)} participants for session {session_id}")
            return participants
        except aiosqlite.Error as e:
            db_logger.error(f"Database error while fetching session participants: {e}", exc_info=True)
            raise
        except Exception as e:
            db_logger.error(f"Unexpected error while fetching session participants: {e}", exc_info=True)
            raise

async def leave_session(session_id: int, user_id: int):
    db_logger.info(f"Attempting to remove user from session. Session ID: {session_id}, User ID: {user_id}")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("DELETE FROM participants WHERE session_id = ? AND user_id = ?", (session_id, user_id))
            await db.commit()
            db_logger.info(f"User {user_id} successfully left session {session_id}")
        except aiosqlite.Error as e:
            db_logger.error(f"Database error while leaving session: {e}", exc_info=True)
            raise
        except Exception as e:
            db_logger.error(f"Unexpected error while leaving session: {e}", exc_info=True)
            raise


async def get_blocked_users():
    db_logger.info("Fetching list of blocked users")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT id, name, block_reason FROM users WHERE is_blocked = 1") as cursor:
                blocked_users = await cursor.fetchall()
            db_logger.info(f"Retrieved {len(blocked_users)} blocked users")
            return blocked_users
        except aiosqlite.Error as e:
            db_logger.error(f"Database error while fetching blocked users: {e}", exc_info=True)
            raise
        except Exception as e:
            db_logger.error(f"Unexpected error while fetching blocked users: {e}", exc_info=True)
            raise

async def is_user_blocked(user_id: int) -> bool:
    db_logger.info(f"Checking if user {user_id} is blocked")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            async with db.execute("SELECT is_blocked FROM users WHERE id = ?", (user_id,)) as cursor:
                result = await cursor.fetchone()
                is_blocked = result[0] if result else False
            db_logger.info(f"User {user_id} blocked status: {is_blocked}")
            return is_blocked
        except aiosqlite.Error as e:
            db_logger.error(f"Database error while checking user blocked status: {e}", exc_info=True)
            raise
        except Exception as e:
            db_logger.error(f"Unexpected error while checking user blocked status: {e}", exc_info=True)
            raise

async def get_all_users():
    db_logger.info("Fetching all users")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT id, name, age FROM users") as cursor:
                users = await cursor.fetchall()
            db_logger.info(f"Retrieved {len(users)} users")
            return users
        except aiosqlite.Error as e:
            db_logger.error(f"Database error while fetching all users: {e}", exc_info=True)
            raise
        except Exception as e:
            db_logger.error(f"Unexpected error while fetching all users: {e}", exc_info=True)
            raise

async def block_user(user_id: int, reason: str):
    db_logger.info(f"Attempting to block user {user_id}. Reason: {reason}")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("UPDATE users SET is_blocked = 1, block_reason = ? WHERE id = ?", (reason, user_id))
            await db.commit()
            db_logger.info(f"User {user_id} has been successfully blocked")
        except aiosqlite.Error as e:
            db_logger.error(f"Database error while blocking user: {e}", exc_info=True)
            raise
        except Exception as e:
            db_logger.error(f"Unexpected error while blocking user: {e}", exc_info=True)
            raise

async def unblock_user(user_id: int):
    db_logger.info(f"Attempting to unblock user {user_id}")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("UPDATE users SET is_blocked = 0, block_reason = NULL WHERE id = ?", (user_id,))
            await db.commit()
            db_logger.info(f"User {user_id} has been successfully unblocked")
        except aiosqlite.Error as e:
            db_logger.error(f"Database error while unblocking user: {e}", exc_info=True)
            raise
        except Exception as e:
            db_logger.error(f"Unexpected error while unblocking user: {e}", exc_info=True)
            raise


async def get_user_statistics():
    db_logger.info("Fetching user statistics")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                total_users = (await cursor.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM users WHERE is_blocked = 0") as cursor:
                active_users = (await cursor.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM users WHERE is_blocked = 1") as cursor:
                blocked_users = (await cursor.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM sessions") as cursor:
                total_sessions = (await cursor.fetchone())[0]

            avg_sessions_per_user = total_sessions / total_users if total_users > 0 else 0

            stats = {
                "total_users": total_users,
                "active_users": active_users,
                "blocked_users": blocked_users,
                "total_sessions": total_sessions,
                "avg_sessions_per_user": avg_sessions_per_user
            }
            db_logger.info(f"User statistics retrieved: {stats}")
            return stats
        except aiosqlite.Error as e:
            db_logger.error(f"Database error while fetching user statistics: {e}", exc_info=True)
            raise
        except Exception as e:
            db_logger.error(f"Unexpected error while fetching user statistics: {e}", exc_info=True)
            raise


async def get_user_info(user_id: int) -> Optional[Dict[str, any]]:
    db_logger.info(f"Fetching info for user {user_id}")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        try:
            async with db.execute("SELECT name, age FROM users WHERE id = ?", (user_id,)) as cursor:
                user = await cursor.fetchone()

            if not user:
                db_logger.warning(f"No user found with ID {user_id}")
                return None

            async with db.execute("SELECT COUNT(*) as created_sessions FROM sessions WHERE creator_id = ?",
                                  (user_id,)) as cursor:
                created_sessions = (await cursor.fetchone())['created_sessions']

            async with db.execute("SELECT COUNT(*) as attended_sessions FROM participants WHERE user_id = ?",
                                  (user_id,)) as cursor:
                attended_sessions = (await cursor.fetchone())['attended_sessions']

            user_info = {
                'name': user['name'],
                'age': user['age'],
                'created_sessions': created_sessions,
                'attended_sessions': attended_sessions
            }
            db_logger.info(f"User info retrieved for user {user_id}: {user_info}")
            return user_info
        except aiosqlite.Error as e:
            db_logger.error(f"Database error while fetching user info: {e}", exc_info=True)
            raise
        except Exception as e:
            db_logger.error(f"Unexpected error while fetching user info: {e}", exc_info=True)
            raise


async def get_user_sessions(user_id: int) -> Optional[List[Dict[str, any]]]:
    db_logger.info(f"Fetching sessions for user {user_id}")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        try:
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")

            async with db.execute("""
                SELECT id, game, date, time, max_players, 
                       (SELECT COUNT(*) FROM participants WHERE session_id = sessions.id) as current_players,
                       creator_id = ? as is_creator
                FROM sessions
                WHERE (creator_id = ? OR id IN (SELECT session_id FROM participants WHERE user_id = ?))
                AND datetime(date || ' ' || time) >= datetime(?)
                ORDER BY date ASC, time ASC
            """, (user_id, user_id, user_id, current_datetime)) as cursor:
                sessions = await cursor.fetchall()

            all_sessions = [dict(session) for session in sessions]

            db_logger.info(f"Retrieved {len(all_sessions)} sessions for user {user_id}")
            return all_sessions
        except aiosqlite.Error as e:
            db_logger.error(f"Database error while fetching user sessions: {e}", exc_info=True)
            raise
        except Exception as e:
            db_logger.error(f"Unexpected error while fetching user sessions: {e}", exc_info=True)
            raise


async def get_upcoming_sessions(hours_before=2):
    db_logger.info(f"Fetching upcoming sessions for next {hours_before} hours")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            future_time = (datetime.now() + timedelta(hours=hours_before)).strftime("%Y-%m-%d %H:%M")
            query = """
            SELECT s.id, s.game, s.date, s.time, p.user_id
            FROM sessions s
            JOIN participants p ON s.id = p.session_id
            LEFT JOIN session_confirmations sc ON s.id = sc.session_id AND p.user_id = sc.user_id
            WHERE datetime(s.date || ' ' || s.time) BETWEEN ? AND ?
            AND (sc.status IS NULL OR sc.status = 'pending')
            """
            async with db.execute(query, (current_time, future_time)) as cursor:
                sessions = await cursor.fetchall()
            db_logger.info(f"Retrieved {len(sessions)} upcoming sessions")
            return sessions
        except aiosqlite.Error as e:
            db_logger.error(f"Database error while fetching upcoming sessions: {e}", exc_info=True)
            raise
        except Exception as e:
            db_logger.error(f"Unexpected error while fetching upcoming sessions: {e}", exc_info=True)
            raise


async def update_session_confirmation(session_id: int, user_id: int, status: str):
    db_logger.info(f"Updating session confirmation. Session ID: {session_id}, User ID: {user_id}, Status: {status}")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("""
            INSERT INTO session_confirmations (session_id, user_id, status)
            VALUES (?, ?, ?)
            ON CONFLICT(session_id, user_id) DO UPDATE SET status = ?
            """, (session_id, user_id, status, status))
            await db.commit()
            db_logger.info(f"Session confirmation updated successfully for session {session_id} and user {user_id}")
        except aiosqlite.Error as e:
            db_logger.error(f"Database error while updating session confirmation: {e}", exc_info=True)
            raise
        except Exception as e:
            db_logger.error(f"Unexpected error while updating session confirmation: {e}", exc_info=True)
            raise

async def remove_participant(session_id: int, user_id: int):
    db_logger.info(f"Removing participant. Session ID: {session_id}, User ID: {user_id}")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("DELETE FROM participants WHERE session_id = ? AND user_id = ?", (session_id, user_id))
            await db.commit()
            db_logger.info(f"Participant (User ID: {user_id}) removed successfully from session {session_id}")
        except aiosqlite.Error as e:
            db_logger.error(f"Database error while removing participant: {e}", exc_info=True)
            raise
        except Exception as e:
            db_logger.error(f"Unexpected error while removing participant: {e}", exc_info=True)
            raise

async def get_session_participants(session_id: int):
    db_logger.info(f"Fetching participants for session ID: {session_id}")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        try:
            async with db.execute("""
                SELECT u.id, u.name, u.username
                FROM participants p
                JOIN users u ON p.user_id = u.id
                WHERE p.session_id = ?
            """, (session_id,)) as cursor:
                participants = await cursor.fetchall()
            db_logger.info(f"Retrieved {len(participants)} participants for session {session_id}")
            return participants
        except aiosqlite.Error as e:
            db_logger.error(f"Database error while fetching session participants: {e}", exc_info=True)
            raise
        except Exception as e:
            db_logger.error(f"Unexpected error while fetching session participants: {e}", exc_info=True)
            raise

async def get_session_info(session_id: int) -> Optional[Dict[str, any]]:
    db_logger.info(f"Fetching info for session ID: {session_id}")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        try:
            async with db.execute("""
                SELECT s.id, s.game, s.date, s.time, s.max_players, s.creator_id, u.name as creator_name
                FROM sessions s
                JOIN users u ON s.creator_id = u.id
                WHERE s.id = ?
            """, (session_id,)) as cursor:
                session = await cursor.fetchone()
            if session:
                session_dict = dict(session)
                db_logger.info(f"Session info retrieved for session {session_id}: {session_dict}")
                return session_dict
            else:
                db_logger.warning(f"No session found with ID {session_id}")
                return None
        except aiosqlite.Error as e:
            db_logger.error(f"Database error while fetching session info: {e}", exc_info=True)
            raise
        except Exception as e:
            db_logger.error(f"Unexpected error while fetching session info: {e}", exc_info=True)
            raise

async def update_user_info(user_id: int, name: str = None, age: int = None):
    db_logger.info(f"Updating user info for user {user_id}")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            if name is not None:
                await db.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
            if age is not None:
                await db.execute("UPDATE users SET age = ? WHERE id = ?", (age, user_id))
            await db.commit()
            db_logger.info(f"User info updated successfully for user {user_id}")
        except aiosqlite.Error as e:
            db_logger.error(f"Database error while updating user info: {e}", exc_info=True)
            raise
        except Exception as e:
            db_logger.error(f"Unexpected error while updating user info: {e}", exc_info=True)
            raise


async def delete_session(session_id: int, user_id: int) -> bool:
    db_logger.info(f"Attempting to delete session {session_id} by user {user_id}")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            # Проверяем, является ли пользователь создателем сессии
            async with db.execute("SELECT creator_id FROM sessions WHERE id = ?", (session_id,)) as cursor:
                result = await cursor.fetchone()
                if not result or result[0] != user_id:
                    db_logger.warning(f"User {user_id} attempted to delete session {session_id} without permission")
                    return False

            # Удаляем записи из таблицы participants
            await db.execute("DELETE FROM participants WHERE session_id = ?", (session_id,))

            # Удаляем записи из таблицы session_confirmations
            await db.execute("DELETE FROM session_confirmations WHERE session_id = ?", (session_id,))

            # Удаляем саму сессию
            await db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

            await db.commit()
            db_logger.info(f"Successfully deleted session {session_id}")
            return True
        except Exception as e:
            db_logger.error(f"Error deleting session {session_id}: {e}", exc_info=True)
            return False

async def get_user_session_history(user_id: int):
    db_logger.info(f"Fetching session history for user {user_id}")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        try:
            query = """
            WITH current_sessions AS (
                SELECT DISTINCT session_id
                FROM participants
                WHERE user_id = ? AND session_id IN (
                    SELECT id FROM sessions WHERE date >= date('now')
                )
                EXCEPT
                SELECT session_id
                FROM user_session_events
                WHERE user_id = ? AND event_type = 'left'
            )
            SELECT use.session_id, use.event_type, use.timestamp, u.name as user_name, s.game
            FROM user_session_events use
            JOIN sessions s ON use.session_id = s.id
            JOIN users u ON use.user_id = u.id
            WHERE use.session_id IN (SELECT session_id FROM current_sessions)
            ORDER BY use.timestamp DESC
            LIMIT 50
            """
            async with db.execute(query, (user_id, user_id)) as cursor:
                history = await cursor.fetchall()
            db_logger.info(f"Retrieved {len(history)} history events for sessions user {user_id} is currently participating in")
            return [dict(event) for event in history]
        except aiosqlite.Error as e:
            db_logger.error(f"Database error while fetching user session history: {e}", exc_info=True)
            raise
        except Exception as e:
            db_logger.error(f"Unexpected error while fetching user session history: {e}", exc_info=True)
            raise

async def add_user_session_event(user_id: int, session_id: int, event_type: str):
    db_logger.info(f"Adding session event for user {user_id}, session {session_id}, event type: {event_type}")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("""
                INSERT INTO user_session_events (user_id, session_id, event_type)
                VALUES (?, ?, ?)
            """, (user_id, session_id, event_type))
            await db.commit()
            db_logger.info(f"Session event added successfully")
        except aiosqlite.Error as e:
            db_logger.error(f"Database error while adding session event: {e}", exc_info=True)
            raise
        except Exception as e:
            db_logger.error(f"Unexpected error while adding session event: {e}", exc_info=True)
            raise