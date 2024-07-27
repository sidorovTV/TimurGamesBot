import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import aiosqlite
DATABASE_PATH = 'data/TGB.sqlite'


def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, name TEXT, age INTEGER, username TEXT, is_blocked INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sessions
                 (id INTEGER PRIMARY KEY, game TEXT, date TEXT, time TEXT, max_players INTEGER, creator_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS participants
                 (session_id INTEGER, user_id INTEGER, PRIMARY KEY (session_id, user_id))''')
    conn.commit()
    conn.close()


def save_user(name: str, age: int, username: str, user_id: int):
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (id, name, age, username) VALUES (?, ?, ?, ?)",
              (user_id, name, age, username))
    conn.commit()
    conn.close()


async def is_user_registered(user_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT id FROM users WHERE id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()
            return result is not None


def create_session(game: str, date: str, time: str, max_players: int, creator_id: int) -> int:
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO sessions (game, date, time, max_players, creator_id) VALUES (?, ?, ?, ?, ?)",
              (game, date, time, max_players, creator_id))
    session_id = c.lastrowid
    conn.commit()
    conn.close()
    print(f"Debug: Created session with ID: {session_id}")  # Добавьте эту строку
    return session_id



def join_session(session_id: int, user_id: int):
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO participants (session_id, user_id) VALUES (?, ?)", (session_id, user_id))
    conn.commit()
    conn.close()


def get_sessions():
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT s.id, s.game, s.date, s.time, s.max_players, 
               COUNT(p.user_id) as current_players, u.name as creator_name
        FROM sessions s
        LEFT JOIN participants p ON s.id = p.session_id
        JOIN users u ON s.creator_id = u.id
        WHERE s.date >= date('now')
        GROUP BY s.id
        ORDER BY s.date, s.time
    """)
    sessions = c.fetchall()
    conn.close()
    print(f"Debug: Retrieved sessions: {sessions}")  # Добавьте эту строку
    return sessions


def get_session_participants(session_id: int):
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT u.id, u.name, u.username
        FROM participants p
        JOIN users u ON p.user_id = u.id
        WHERE p.session_id = ?
    """, (session_id,))
    participants = c.fetchall()
    conn.close()
    return participants

def leave_session(session_id: int, user_id: int):
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM participants WHERE session_id = ? AND user_id = ?", (session_id, user_id))
    conn.commit()
    conn.close()


def get_blocked_users():
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, block_reason FROM users WHERE is_blocked = 1")
    blocked_users = c.fetchall()
    conn.close()
    return blocked_users

async def is_user_blocked(user_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT is_blocked FROM users WHERE id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else False

def get_all_users():
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, age FROM users")
    users = c.fetchall()
    conn.close()
    return users


def block_user(user_id: int, reason: str):
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET is_blocked = 1, block_reason = ? WHERE id = ?", (reason, user_id))
    conn.commit()
    conn.close()


def unblock_user(user_id: int):
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET is_blocked = 0, block_reason = NULL WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_user_statistics():
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM users WHERE is_blocked = 0")
    active_users = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM users WHERE is_blocked = 1")
    blocked_users = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM sessions")
    total_sessions = c.fetchone()[0]

    avg_sessions_per_user = total_sessions / total_users if total_users > 0 else 0

    conn.close()

    return {
        "total_users": total_users,
        "active_users": active_users,
        "blocked_users": blocked_users,
        "total_sessions": total_sessions,
        "avg_sessions_per_user": avg_sessions_per_user
    }


async def get_user_info(user_id: int) -> Optional[Dict[str, any]]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row

        try:
            # Получаем основную информацию о пользователе
            async with db.execute("""
                SELECT name, age
                FROM users
                WHERE id = ?
            """, (user_id,)) as cursor:
                user = await cursor.fetchone()

            if not user:
                return None

            # Получаем количество созданных сессий
            async with db.execute("""
                SELECT COUNT(*) as created_sessions
                FROM sessions
                WHERE creator_id = ?
            """, (user_id,)) as cursor:
                created_sessions = (await cursor.fetchone())['created_sessions']

            # Получаем количество посещенных сессий
            async with db.execute("""
                SELECT COUNT(*) as attended_sessions
                FROM participants
                WHERE user_id = ?
            """, (user_id,)) as cursor:
                attended_sessions = (await cursor.fetchone())['attended_sessions']

            return {
                'name': user['name'],
                'age': user['age'],
                'created_sessions': created_sessions,
                'attended_sessions': attended_sessions
            }

        except aiosqlite.Error as e:
            print(f"Database error: {e}")
            return None



def get_user_sessions(user_id: int) -> Optional[List[Dict[str, any]]]:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Это позволит обращаться к результатам по именам столбцов
    c = conn.cursor()

    try:
        # Получаем сессии, созданные пользователем
        c.execute("""
            SELECT id, game, date, time, max_players, 
                   (SELECT COUNT(*) FROM participants WHERE session_id = sessions.id) as current_players
            FROM sessions
            WHERE creator_id = ?
            ORDER BY date DESC, time DESC
        """, (user_id,))
        created_sessions = c.fetchall()

        # Получаем сессии, в которых пользователь участвует
        c.execute("""
            SELECT s.id, s.game, s.date, s.time, s.max_players,
                   (SELECT COUNT(*) FROM participants WHERE session_id = s.id) as current_players
            FROM sessions s
            JOIN participants p ON s.id = p.session_id
            WHERE p.user_id = ? AND s.creator_id != ?
            ORDER BY s.date DESC, s.time DESC
        """, (user_id, user_id))
        participated_sessions = c.fetchall()

        # Объединяем результаты
        all_sessions = []
        for session in created_sessions:
            all_sessions.append({
                'id': session['id'],
                'game': session['game'],
                'date': session['date'],
                'time': session['time'],
                'max_players': session['max_players'],
                'current_players': session['current_players'],
                'is_creator': True
            })

        for session in participated_sessions:
            all_sessions.append({
                'id': session['id'],
                'game': session['game'],
                'date': session['date'],
                'time': session['time'],
                'max_players': session['max_players'],
                'current_players': session['current_players'],
                'is_creator': False
            })

        # Сортируем все сессии по дате и времени
        all_sessions.sort(key=lambda x: (x['date'], x['time']), reverse=True)

        return all_sessions

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None

    finally:
        conn.close()