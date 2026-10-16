import os
import threading
import time
from config import *
from logic import *
import schedule
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

bot = TeleBot(API_TOKEN)
manager = DatabaseManager(DATABASE)


def gen_markup(id):
  markup = InlineKeyboardMarkup()
  markup.row_width = 1
  markup.add(InlineKeyboardButton('Получить!', callback_data=str(id)))
  return markup


def send_message():
  prize_data = manager.get_random_prize()
  if not prize_data:
    return
  prize_id, img = prize_data
  manager.mark_prize_used(prize_id)
  hide_img(img)
  for user in manager.get_users():
    if os.path.exists(f'hidden_img/{img}'):
      with open(f'hidden_img/{img}', 'rb') as photo:
        bot.send_photo(user, photo, reply_markup=gen_markup(id=prize_id))


def shedule_thread():
  schedule.every().minute.do(send_message)
  while True:
    schedule.run_pending()
    time.sleep(1)


@bot.message_handler(commands=['start'])
def handle_start(message):
  user_id = message.chat.id
  if user_id in manager.get_users():
    bot.reply_to(message, 'Ты уже зарегистрирован!')
  else:
    manager.add_user(user_id, message.from_user.username)
    bot.reply_to(
        message,
        """Привет! Добро пожаловать! 
Тебя успешно зарегистрировали!
Каждую минуту будут приходить новые картинки. Нажимай 'Получить!' раньше всех!
За победу ты получаешь приз и +10 монеток 💰!
Проверить баланс: /balance""",
    )


@bot.message_handler(commands=['rating'])
def handle_rating(message):
  res = manager.get_rating()
  if not res:
    bot.send_message(message.chat.id, 'Рейтинг пока пуст!')
    return
  res_list = [f'| @{x[0]:<11} | {x[1]:<11}|\n' + '_' * 26 for x in res]
  res_str = '\n'.join(res_list)
  res_str = f'|USER_NAME    |COUNT_PRIZE|\n' + '_' * 26 + '\n' + res_str
  bot.send_message(message.chat.id, res_str)


# --- Команда для просмотра баланса монеток ---
@bot.message_handler(commands=['balance'])
def handle_balance(message):
  user_id = message.chat.id
  points = manager.get_points(user_id)
  bot.send_message(message.chat.id, f'💰 Твой баланс: {points} монеток!')


# Единый обработчик нажатия кнопки "Получить!"
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
  prize_id = call.data
  user_id = call.message.chat.id

  if manager.get_winners_count(prize_id) < 3:
    res = manager.add_winner(user_id, prize_id)
    if res:
      manager.add_points(user_id, 10)  # Начисляем 10 монеток
      img = manager.get_prize_img(prize_id)
      if img and os.path.exists(f'img/{img}'):
        with open(f'img/{img}', 'rb') as photo:
          bot.send_photo(
              user_id,
              photo,
              caption=(
                  '🎉 Поздравляем! Ты получил картинку и +10 монеток 💰!\nПроверь'
                  ' баланс: /balance'
              ),
          )
      bot.answer_callback_query(call.id, 'Успешно!')
    else:
      bot.answer_callback_query(call.id, 'Ты уже забирал этот приз!')
      bot.send_message(user_id, 'Ты уже получил эту картинку!')
  else:
    bot.answer_callback_query(call.id, 'Призы закончились!')
    bot.send_message(
        user_id,
        'К сожалению, ты не успел получить картинку! Попробуй в следующий раз!',
    )


def polling_thread():
  bot.polling(none_stop=True)


if __name__ == '__main__':
  manager.create_tables()

  t_polling = threading.Thread(target=polling_thread)
  t_schedule = threading.Thread(target=shedule_thread)

  t_polling.start()
  t_schedule.start()