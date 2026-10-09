import sqlite3
conn = sqlite3.connect('movie.db')
cursor = conn.cursor()

cursor.execute(
    'SELECT title, budget FROM movies ORDER BY popularity DESC LIMIT 1;'
)
res1 = cursor.fetchone()
print(f'1. Самый популярный фильм: {res1[0]}, бюджет: {res1[1]}')

cursor.execute(
    "SELECT title FROM movies WHERE release_date LIKE '2009-12%' ORDER BY"
    ' budget DESC LIMIT 1;'
)
res2 = cursor.fetchone()
print(f'2. Самый дорогой фильм декабря 2009: {res2[0]}')


cursor.execute("SELECT title FROM movies WHERE tagline = 'The battle within.';")
res3 = cursor.fetchone()
print(f'3. Фильм со слоганом "The battle within.": {res3[0]}')

cursor.execute(
    "SELECT title FROM movies WHERE release_date < '1980-01-01' AND"
    ' vote_average > 8 ORDER BY vote_count DESC LIMIT 1;'
)
res4 = cursor.fetchone()
print(f'4. Фильм до 1980 года с рейтингом > 8 и макс. голосов: {res4[0]}')

conn.close()