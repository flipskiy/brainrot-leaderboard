from flask import Flask, request, jsonify
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)

# Подключение к базе данных
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db():
    return psycopg2.connect(DATABASE_URL)

# Создаём таблицу при первом запуске
def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS players (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            total_clicks BIGINT DEFAULT 0,
            balance BIGINT DEFAULT 0,
            level INTEGER DEFAULT 1,
            prestige INTEGER DEFAULT 0,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

@app.route('/api/save', methods=['POST'])
def save_score():
    """Сохранить результат игрока"""
    data = request.json
    user_id = data.get('user_id')
    username = data.get('username', '')
    first_name = data.get('first_name', '')
    last_name = data.get('last_name', '')
    total_clicks = data.get('total_clicks', 0)
    balance = data.get('balance', 0)
    level = data.get('level', 1)
    prestige = data.get('prestige', 0)
    
    conn = get_db()
    cur = conn.cursor()
    
    # Вставляем или обновляем игрока
    cur.execute('''
        INSERT INTO players (user_id, username, first_name, last_name, total_clicks, balance, level, prestige, last_update)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
            username = EXCLUDED.username,
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            total_clicks = EXCLUDED.total_clicks,
            balance = EXCLUDED.balance,
            level = EXCLUDED.level,
            prestige = EXCLUDED.prestige,
            last_update = EXCLUDED.last_update
    ''', (user_id, username, first_name, last_name, total_clicks, balance, level, prestige, datetime.now()))
    
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'status': 'ok'})

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """Получить топ-100 игроков"""
    sort_by = request.args.get('sort', 'total_clicks')  # total_clicks, balance, level, prestige
    
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute(f'''
        SELECT user_id, username, first_name, last_name, total_clicks, balance, level, prestige
        FROM players
        ORDER BY {sort_by} DESC
        LIMIT 100
    ''')
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    leaderboard = []
    for i, row in enumerate(rows, 1):
        leaderboard.append({
            'rank': i,
            'user_id': row[0],
            'username': row[1] or row[2] or 'Игрок',
            'first_name': row[2],
            'last_name': row[3],
            'total_clicks': row[4],
            'balance': row[5],
            'level': row[6],
            'prestige': row[7]
        })
    
    return jsonify(leaderboard)

@app.route('/api/player/<int:user_id>', methods=['GET'])
def get_player(user_id):
    """Получить данные конкретного игрока"""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT user_id, username, first_name, last_name, total_clicks, balance, level, prestige
        FROM players
        WHERE user_id = %s
    ''', (user_id,))
    
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if row:
        return jsonify({
            'user_id': row[0],
            'username': row[1] or row[2] or 'Игрок',
            'first_name': row[2],
            'last_name': row[3],
            'total_clicks': row[4],
            'balance': row[5],
            'level': row[6],
            'prestige': row[7]
        })
    else:
        return jsonify({'error': 'Player not found'}), 404

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)