import logging
import os
from urllib import response

import psycopg2
import aiogram
from aiogram.dispatcher.filters import state
from aiogram.dispatcher.filters.state import StatesGroup, State

print((aiogram.__version__))

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, CallbackQuery, callback_query
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext

# инициализация логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# создание отдельных файлов для логов ошибок и предупреждений
errors_handler = logging.FileHandler(os.path.join(os.getcwd(), 'errors.log'))
warnings_handler = logging.FileHandler(os.path.join(os.getcwd(), 'warnings.log'))
errors_handler.setLevel(logging.ERROR)
warnings_handler.setLevel(logging.WARNING)

# создание отдельных форматов для логов
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
errors_handler.setFormatter(formatter)
warnings_handler.setFormatter(formatter)

# добавление обработчиков в логгер
logger.addHandler(errors_handler)
logger.addHandler(warnings_handler)

# инициализация бота и диспетчера
TOKEN = '6293413845:AAGLJ1k1k7Cs7_-lto-mqhGSNScps1Ax8qQ'
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# инициализация подключения к базе данных PostgreSQL
db_host = 'localhost'
db_port = '5432'
db_name = 'telegram_botdb'
db_user = 'postgres'
db_password = 'root'
conn = psycopg2.connect(host=db_host, port=db_port, dbname=db_name, user=db_user, password=db_password)


class Form(StatesGroup):
    amount = State()
    invoice_payload = State()
    shipping_option_id = State()


# функция для получения баланса пользователя из базы данных
def get_user_balance(user_id):
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE user_id = %s", (user_id,))
    balance = cur.fetchone()
    conn.commit()
    cur.close()
    if balance:
        return balance[0]
    else:
        return 0


# функция для изменения баланса пользователя в базе данных
def update_user_balance(user_id, balance_diff):
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (balance_diff, user_id))
    conn.commit()
    cur.close()


# функция для блокировки пользователя в базе данных
def block_user(user_id):
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_blocked = true WHERE user_id = %s", (user_id,))
    conn.commit()
    cur.close()


# функция для разблокировки пользователя в базе данных
def unblock_user(user_id):
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_blocked = false WHERE user_id = %s", (user_id,))
    conn.commit()
    cur.close()


# функция для проверки, заблокирован ли пользователь
def is_user_blocked(user_id):
    cur = conn.cursor()
    cur.execute("SELECT is_blocked FROM users WHERE user_id = %s", (user_id,))
    is_blocked = cur.fetchone()
    conn.commit()
    cur.close()
    if is_blocked:
        return is_blocked[0]
    else:
        return False


# обработчик команды /start
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    # получаем имя пользователя
    user_name = message.from_user.first_name
    # отправляем шаблонное сообщение
    await message.answer(f"Привет, {user_name}\n\n"
                         "Я - бот для пополнения баланса.\n"
                         "Нажмите на кнопку, чтобы пополнить баланс",
                         reply_markup=InlineKeyboardMarkup(
                             inline_keyboard=[
                                 [
                                     InlineKeyboardButton(text="Пополнить баланс", callback_data="top_up_balance")
                                 ]
                             ]
                         ))

    # обработчик нажатия на кнопку пополнения баланса
    @dp.callback_query_handler(lambda query: query.data == 'top_up_balance')
    async def top_up_balance_callback(query: CallbackQuery, state: FSMContext):
        await bot.answer_callback_query(query.id)
        await bot.send_message(query.message.chat.id, 'Введите сумму, на которую вы хотите пополнить баланс')
        async with state.proxy() as data:
            data['user_id'] = query.message.chat.id
        await Form.amount.set()
        try:
            # создаем платежный счет и отправляем ссылку на оплату
            print(dir(response))
            response = await some_async_request()
            text_response = await response.read()
            price = types.LabeledPrice(label='Пополнение баланса', amount=int(text_response) * 100)
            print(price)
            currency = 'RUB'
            title = 'Пополнение баланса'
            description = 'Пополнение баланса в телеграм-боте'
            provider_token = 'TEST:58647'
            start_parameter = 'top_up_balance'
            payload = str(callback_query.from_user.id)
            invoice = await bot.send_invoice(chat_id=callback_query.from_user.id,
                                             title=title,
                                             description=description,
                                             payload=payload,
                                             provider_token=provider_token,
                                             currency=currency,
                                             prices=[price],
                                             start_parameter=start_parameter,
                                             photo_url=None,
                                             photo_size=None,
                                             photo_width=None,
                                             photo_height=None)
            # отправляем сообщение об успешном создании счета и кнопки для проверки статуса оплаты
            await bot.send_message(chat_id=callback_query.from_user.id, text="Счет для оплаты создан")
            await bot.send_message(chat_id=callback_query.from_user.id, text="Проверить статус оплаты:",
                                   reply_markup=InlineKeyboardMarkup(
                                       inline_keyboard=[
                                           [
                                               InlineKeyboardButton(text="Проверить",
                                                                    callback_data=f"check_payment_{invoice.invoice_message_id}")
                                           ]
                                       ]
                                   ))
        except Exception as e:
            # отправляем сообщение об ошибке и логгируем ее
            await bot.send_message(chat_id=callback_query.message.chat.id, text="Ошибка при создании счета для оплаты")
            print(dir(callback_query))
            logger.error(f"Error creating invoice for user_id {callback_query.from_user.id}: {e}")

    # обработчик нажатия на кнопку проверки статуса оплаты
    @dp.callback_query_handler(lambda query: query.data.startswith('check_payment_'))
    async def check_payment_callback(callback_query: types.CallbackQuery):
        # удаляем сообщение с кнопкой
        await bot.answer_callback_query(callback_query.id)
        await bot.delete_message(chat_id=callback_query.message.chat.id,
                                 message_id=callback_query.message.message_id)
        # получаем id сообщения счета
        invoice_message_id = int(callback_query.data.split('_')[2])
        # получаем информацию о счете
        invoice_info = await bot.get_invoice(chat_id=callback_query.from_user.id, message_id=invoice_message_id)
        try:
            # получаем информацию о платеже
            payment_info = await bot.get_payment(invoice_info.invoice_payload)
            if payment_info.successful:
                # обновляем баланс пользователя в базе данных и отправляем успешное сообщение
                update_user_balance(callback_query.from_user.id, payment_info.total_amount // 100)
                await bot.send_message(chat_id=callback_query.from_user.id, text="Платеж успешно проведен")
            else:
                # отправляем сообщение о неудачном платеже
                await bot.send_message(chat_id=callback_query.from_user.id, text="Платеж не был проведен")
        except Exception as e:
            # отправляем сообщение об ошибке и логгируем ее
            await bot.send_message(chat_id=callback_query.from_user.id,
                                   text="Ошибка при получении информации о платеже")
            logger.error(f"Error getting payment info for user_id {callback_query.from_user.id}: {e}")

        # обработчик команды /admin
        @dp.message_handler(commands=['admin'])
        async def admin_command(message: types.Message):
            # проверяем, является ли пользователь администратором
            if message.from_user.id != AdminUser.id:
                await message.answer(f"У вас нет доступа к админ-панели")
                return
            # отправляем главное меню админки
            await message.answer(f"Главное меню админ-панели",
                                 reply_markup=InlineKeyboardMarkup(
                                     inline_keyboard=[
                                         [
                                             InlineKeyboardButton(text="Пользователи", callback_data="users"),
                                             InlineKeyboardButton(text="Логи", callback_data="logs")
                                         ]
                                     ]
                                 ))

        # обработчик нажатия на кнопку "Пользователи" в админ-панели
        @dp.callback_query_handler(lambda query: query.data == 'users')
        async def users_callback(callback_query: types.CallbackQuery):
            # удаляем сообщение с кнопкой и отправляем список пользователей и их балансов
            await bot.answer_callback_query(callback_query.id)
            await bot.delete_message(chat_id=callback_query.message.chat.id,
                                     message_id=callback_query.message.message_id)
            cur = conn.cursor()
            cur.execute("SELECT user_id, balance FROM users")
            users = cur.fetchall()
            conn.commit()
            cur.close()
            users_list = ''
            for user in users:
                users_list += f"{user[0]}: {user[1]}\n"
            await bot.send_message(chat_id=callback_query.from_user.id, text=f"Пользователи:\n{users_list}")

        # обработчик нажатия на кнопку "Логи" в админ-панели
        @dp.callback_query_handler(lambda query: query.data == 'logs')
        async def logs_callback(callback_query: types.CallbackQuery):
            # удаляем сообщение с кнопкой и отправляем файлы логов
            await bot.answer_callback_query(callback_query.id)
            await bot.delete_message(chat_id=callback_query.message.chat.id,
                                     message_id=callback_query.message.message_id)
            with open(os.path.join(os.getcwd(), 'errors.log'), 'rb') as f:
                await bot.send_document(chat_id=callback_query.from_user.id, document=f, caption="Файл логов ошибок")
            with open(os.path.join(os.getcwd(), 'warnings.log'), 'rb') as f:
                await bot.send_document(chat_id=callback_query.from_user.id, document=f,
                                        caption="Файл логов предупреждений")

        # запуск бота

if __name__ == '__main__':
        AdminUser = 'YOUR_ADMIN_USER_ID'
        conn.set_session(autocommit=True)
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS users(user_id bigint PRIMARY KEY, balance integer, is_blocked boolean DEFAULT false)")
        conn.commit()
        cur.close()
        executor.start_polling(dp, skip_updates=True)