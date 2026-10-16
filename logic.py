from datetime import datetime
import os
import sqlite3
from config import DATABASE
import cv2


class DatabaseManager:

  def __init__(self, database):
    self.database = database

  def create_tables(self):
    conn = sqlite3.connect(self.database)
    with conn:
      # Таблица пользователей с колонкой points (монетки)
      conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                user_name TEXT,
                points INTEGER DEFAULT 0
            )
            ''')
      conn.execute('''
            CREATE TABLE IF NOT EXISTS prizes (
                prize_id INTEGER PRIMARY KEY,
                image TEXT,
                used INTEGER DEFAULT 0
            )
            ''')
      conn.execute('''
            CREATE TABLE IF NOT EXISTS winners (
                user_id INTEGER,
                prize_id INTEGER,
                win_time TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id),
                FOREIGN KEY(prize_id) REFERENCES prizes(prize_id)
            )
            ''')

  def add_user(self, user_id, user_name):
    conn = sqlite3.connect(self.database)
    with conn:
      conn.execute(
          'INSERT OR IGNORE INTO users (user_id, user_name) VALUES (?, ?)',
          (user_id, user_name),
      )

  def add_prize(self, data):
    conn = sqlite3.connect(self.database)
    with conn:
      conn.executemany('INSERT INTO prizes (image) VALUES (?)', data)

  def add_winner(self, user_id, prize_id):
    win_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(self.database)
    with conn:
      cur = conn.cursor()
      cur.execute(
          'SELECT * FROM winners WHERE user_id = ? AND prize_id = ?',
          (user_id, prize_id),
      )
      if cur.fetchall():
        return 0
      conn.execute(
          'INSERT INTO winners (user_id, prize_id, win_time) VALUES (?, ?, ?)',
          (user_id, prize_id, win_time),
      )
      return 1

  # --- Бонусная система ---
  def add_points(self, user_id, points=10):
    conn = sqlite3.connect(self.database)
    with conn:
      conn.execute(
          'UPDATE users SET points = points + ? WHERE user_id = ?',
          (points, user_id),
      )

  def get_points(self, user_id):
    conn = sqlite3.connect(self.database)
    with conn:
      cur = conn.cursor()
      cur.execute('SELECT points FROM users WHERE user_id = ?', (user_id,))
      res = cur.fetchone()
      return res[0] if res and res[0] is not None else 0

  def mark_prize_used(self, prize_id):
    conn = sqlite3.connect(self.database)
    with conn:
      conn.execute(
          'UPDATE prizes SET used = 1 WHERE prize_id = ?', (prize_id,)
      )

  def get_winners_count(self, prize_id):
    conn = sqlite3.connect(self.database)
    with conn:
      cur = conn.cursor()
      cur.execute(
          'SELECT COUNT(*) FROM winners WHERE prize_id = ?', (prize_id,)
      )
      return cur.fetchone()[0]

  def get_winners_img(self, user_id):
    conn = sqlite3.connect(self.database)
    with conn:
      cur = conn.cursor()
      cur.execute(
          '''
            SELECT image FROM winners 
            INNER JOIN prizes ON winners.prize_id = prizes.prize_id
            WHERE user_id = ?''',
          (user_id,),
      )
      return cur.fetchall()

  def get_rating(self):
    conn = sqlite3.connect(self.database)
    with conn:
      cur = conn.cursor()
      cur.execute('''
            SELECT users.user_name, COUNT(winners.prize_id) AS total_prizes
            FROM winners
            INNER JOIN users ON users.user_id = winners.user_id
            GROUP BY users.user_id
            ORDER BY total_prizes DESC
            LIMIT 10
        ''')
      return cur.fetchall()

  def get_users(self):
    conn = sqlite3.connect(self.database)
    with conn:
      cur = conn.cursor()
      cur.execute('SELECT user_id FROM users')
      return [x[0] for x in cur.fetchall()]

  def get_prize_img(self, prize_id):
    conn = sqlite3.connect(self.database)
    with conn:
      cur = conn.cursor()
      cur.execute('SELECT image FROM prizes WHERE prize_id = ?', (prize_id,))
      res = cur.fetchone()
      return res[0] if res else None

  def get_random_prize(self):
    conn = sqlite3.connect(self.database)
    with conn:
      cur = conn.cursor()
      cur.execute(
          'SELECT prize_id, image FROM prizes WHERE used = 0 ORDER BY RANDOM()'
          ' LIMIT 1'
      )
      return cur.fetchone()


def hide_img(img_name):
  image = cv2.imread(f'img/{img_name}')
  if image is None:
    return
  blurred_image = cv2.GaussianBlur(image, (15, 15), 0)
  pixelated_image = cv2.resize(
      blurred_image, (30, 30), interpolation=cv2.INTER_NEAREST
  )
  pixelated_image = cv2.resize(
      pixelated_image,
      (image.shape[1], image.shape[0]),
      interpolation=cv2.INTER_NEAREST,
  )
  cv2.imwrite(f'hidden_img/{img_name}', pixelated_image)


if __name__ == '__main__':
  manager = DatabaseManager(DATABASE)
  manager.create_tables()
  if os.path.exists('img'):
    prizes_img = os.listdir('img')
    data = [(x,) for x in prizes_img]
    manager.add_prize(data)