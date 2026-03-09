import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "8675804759:AAHu2xWLMKyUcugOGsAcoTj-ktQx7oAyGvc"
ADMIN_ID = [7242502677]

bot = Bot(TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ================= DATABASE =================

async def init_db():

    async with aiosqlite.connect("database.db") as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS reviews(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        photo TEXT,
        amount TEXT,
        currency TEXT,
        rating INTEGER,
        text TEXT
        )  
        """)
                         
        await db.execute("""
        CREATE TABLE IF NOT EXISTS tickets(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        message TEXT
        )
        """)

        await db.commit()


# ================= STATES =================

class ReviewState(StatesGroup):

    photo = State()
    amount = State()
    currency = State()
    rating = State()
    text = State()
    confirm = State()


class SupportState(StatesGroup):

    message = State()
    reply = State()


# ================= MAIN MENU =================

def main_menu():

    kb = InlineKeyboardBuilder()

    kb.button(text="⭐ Отзывы", callback_data="reviews")
    kb.button(text="✍️ Написать отзыв", callback_data="write_review")

    kb.button(text="🛡 Гарант", url="https://t.me/sjsjsjsjskjdsjjsk/5")
    kb.button(text="🤝 Ручения", url="https://t.me/sjsjsjsjskjdsjjsk/4 ")

    kb.button(text="🔥 Топка", url="https://t.me/sjsjsjsjskjdsjjsk/3")
    kb.button(text="🛍 Shop", url="https://t.me/sjsjsjsjskjdsjjsk/7")
    kb.button(text="💸 Прайс", url="https://t.me/sjsjsjsjskjdsjjsk/6")

    kb.button(text="💬 Чат", url="https://t.me/sjsjsjsjskjdsjjsk/8")
    kb.button(text="📩 Поддержка", callback_data="support")

    kb.adjust(2)

    return kb.as_markup()


# ================= START =================

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "✨ Добро пожаловать!\n\nВыберите раздел 👇",
        reply_markup=main_menu()
    )
# ================= REVIEWS =================

@dp.callback_query(F.data == "reviews")
async def reviews(callback: CallbackQuery):
    async with aiosqlite.connect("database.db") as db:
        async with db.execute("SELECT * FROM reviews ORDER BY id") as cursor:
            rows = await cursor.fetchall()

    if not rows:
        await callback.message.answer("📭 Отзывов пока нет.")
        return

    # Получаем первый отзыв
    r = rows[0]
    stars = "⭐" * r[4]
    
    # Находим его порядковый номер
    async with aiosqlite.connect("database.db") as db:
        async with db.execute(
            "SELECT COUNT(*) FROM reviews WHERE id <= ?", 
            (r[0],)
        ) as cursor:
            total_before = await cursor.fetchone()
            position = total_before[0]
        
        # Общее количество отзывов
        async with db.execute("SELECT COUNT(*) FROM reviews") as cursor:
            total = await cursor.fetchone()
            total_count = total[0]

    kb = InlineKeyboardBuilder()
    
    # Проверяем, есть ли следующий отзыв
    async with aiosqlite.connect("database.db") as db:
        async with db.execute("SELECT COUNT(*) FROM reviews WHERE id > ?", (r[0],)) as cursor:
            next_exists = (await cursor.fetchone())[0] > 0
    
    if next_exists:
        kb.button(text="➡️", callback_data=f"review_next_{r[0]}")
    else:
        kb.button(text="➡️", callback_data="no_more")

    await callback.message.answer_photo(
        r[1],
        caption=f"""
⭐ Отзыв {position}/{total_count}

💰 Сумма: {r[2]} {r[3]}
⭐ Рейтинг: {stars}

📝 {r[5]}
""",
        reply_markup=kb.as_markup()
    )


@dp.callback_query(F.data.startswith("review_next_"))
async def review_next(callback: CallbackQuery):
    current_id = int(callback.data.split("_")[2])

    async with aiosqlite.connect("database.db") as db:
        async with db.execute(
            "SELECT * FROM reviews WHERE id > ? ORDER BY id LIMIT 1",
            (current_id,)
        ) as cursor:
            review = await cursor.fetchone()

    if not review:
        await callback.answer("Это последний отзыв")
        return

    # Находим порядковый номер
    async with aiosqlite.connect("database.db") as db:
        async with db.execute(
            "SELECT COUNT(*) FROM reviews WHERE id <= ?", 
            (review[0],)
        ) as cursor:
            total_before = await cursor.fetchone()
            position = total_before[0]
        
        # Общее количество отзывов
        async with db.execute("SELECT COUNT(*) FROM reviews") as cursor:
            total = await cursor.fetchone()
            total_count = total[0]

    kb = InlineKeyboardBuilder()
    
    # Проверяем наличие предыдущего и следующего
    async with aiosqlite.connect("database.db") as db:
        async with db.execute("SELECT COUNT(*) FROM reviews WHERE id < ?", (review[0],)) as cursor:
            prev_exists = (await cursor.fetchone())[0] > 0
        async with db.execute("SELECT COUNT(*) FROM reviews WHERE id > ?", (review[0],)) as cursor:
            next_exists = (await cursor.fetchone())[0] > 0
    
    if prev_exists:
        kb.button(text="⬅️", callback_data=f"review_back_{review[0]}")
    if next_exists:
        kb.button(text="➡️", callback_data=f"review_next_{review[0]}")
    
    kb.adjust(2)

    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=review[1],
            caption=f"""
⭐ Отзыв {position}/{total_count}

💰 Сумма: {review[2]} {review[3]}
⭐ Рейтинг: {"⭐" * review[4]}

📝 {review[5]}
"""
        ),
        reply_markup=kb.as_markup()
    )


@dp.callback_query(F.data.startswith("review_back_"))
async def review_back(callback: CallbackQuery):
    current_id = int(callback.data.split("_")[2])

    async with aiosqlite.connect("database.db") as db:
        async with db.execute(
            "SELECT * FROM reviews WHERE id < ? ORDER BY id DESC LIMIT 1",
            (current_id,)
        ) as cursor:
            review = await cursor.fetchone()

    if not review:
        await callback.answer("Это первый отзыв")
        return

    # Находим порядковый номер
    async with aiosqlite.connect("database.db") as db:
        async with db.execute(
            "SELECT COUNT(*) FROM reviews WHERE id <= ?", 
            (review[0],)
        ) as cursor:
            total_before = await cursor.fetchone()
            position = total_before[0]
        
        # Общее количество отзывов
        async with db.execute("SELECT COUNT(*) FROM reviews") as cursor:
            total = await cursor.fetchone()
            total_count = total[0]

    kb = InlineKeyboardBuilder()
    
    # Проверяем наличие предыдущего и следующего
    async with aiosqlite.connect("database.db") as db:
        async with db.execute("SELECT COUNT(*) FROM reviews WHERE id < ?", (review[0],)) as cursor:
            prev_exists = (await cursor.fetchone())[0] > 0
        async with db.execute("SELECT COUNT(*) FROM reviews WHERE id > ?", (review[0],)) as cursor:
            next_exists = (await cursor.fetchone())[0] > 0
    
    if prev_exists:
        kb.button(text="⬅️", callback_data=f"review_back_{review[0]}")
    if next_exists:
        kb.button(text="➡️", callback_data=f"review_next_{review[0]}")
    
    kb.adjust(2)

    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=review[1],
            caption=f"""
⭐ Отзыв {position}/{total_count}

💰 Сумма: {review[2]} {review[3]}
⭐ Рейтинг: {"⭐" * review[4]}

📝 {review[5]}
"""
        ),
        reply_markup=kb.as_markup()
    )


@dp.callback_query(F.data == "no_more")
async def no_more_reviews(callback: CallbackQuery):
    await callback.answer("Это единственный отзыв")
# ================= WRITE REVIEW =================

@dp.callback_query(F.data == "write_review")
async def write_review(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📸 Отправьте фото сделки")
    await state.set_state(ReviewState.photo)

@dp.message(ReviewState.photo)
async def review_photo(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("❌ Пожалуйста, отправьте фото.")
        return

    photo_id = message.photo[-1].file_id
    await state.update_data(photo=photo_id)
    
    await message.answer("💰 Введите сумму сделки:")
    await state.set_state(ReviewState.amount)

@dp.message(ReviewState.amount)
async def review_amount(message: Message, state: FSMContext):
    await state.update_data(amount=message.text)

    kb = InlineKeyboardBuilder()
    kb.button(text="💎 TON", callback_data="currency_TON")
    kb.button(text="💲 USD", callback_data="currency_USD")
    kb.button(text="💴 RUB", callback_data="currency_RUB")
    kb.adjust(3)

    await message.answer(
        "💱 Выберите валюту:",
        reply_markup=kb.as_markup()
    )
    await state.set_state(ReviewState.currency)

@dp.callback_query(F.data.startswith("currency_"))
async def review_currency(callback: CallbackQuery, state: FSMContext):
    currency = callback.data.split("_")[1]
    await state.update_data(currency=currency)

    kb = InlineKeyboardBuilder()
    kb.button(text="⭐ 1", callback_data="rate_1")
    kb.button(text="⭐⭐ 2", callback_data="rate_2")
    kb.button(text="⭐⭐⭐ 3", callback_data="rate_3")
    kb.button(text="⭐⭐⭐⭐ 4", callback_data="rate_4")
    kb.button(text="⭐⭐⭐⭐⭐ 5", callback_data="rate_5")
    kb.adjust(3, 2)

    await callback.message.answer(
        "⭐ Выберите рейтинг:",
        reply_markup=kb.as_markup()
    )
    await state.set_state(ReviewState.rating)
    await callback.answer()

@dp.callback_query(F.data.startswith("rate_"))
async def review_rating(callback: CallbackQuery, state: FSMContext):
    rating = callback.data.split("_")[1]
    await state.update_data(rating=rating)
    
    await callback.message.answer("📝 Напишите текст отзыва:")
    await state.set_state(ReviewState.text)
    await callback.answer()

@dp.message(ReviewState.text)
async def review_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    
    # Получаем все данные для предпросмотра
    data = await state.get_data()
    
    # Проверяем, что все необходимые данные есть
    required_fields = ['photo', 'amount', 'currency', 'rating', 'text']
    if not all(field in data for field in required_fields):
        await message.answer("❌ Ошибка: не все данные заполнены. Начните заново.")
        await state.clear()
        return
    
    stars = "⭐" * int(data["rating"])
    
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Опубликовать", callback_data="publish_review")
    kb.button(text="❌ Отмена", callback_data="cancel_review")
    kb.adjust(1)
    
    try:
        await message.answer_photo(
            data["photo"],
            caption=f"""
📋 ПРОВЕРЬТЕ ОТЗЫВ

💰 Сумма: {data['amount']} {data['currency']}
⭐ Рейтинг: {stars}

📝 Текст:
{data['text']}

Всё верно?
""",
            reply_markup=kb.as_markup()
        )
        await state.set_state(ReviewState.confirm)
    except Exception as e:
        await message.answer(f"❌ Ошибка при создании предпросмотра: {e}")
        await state.clear()

@dp.callback_query(F.data == "publish_review")
async def publish_review(callback: CallbackQuery, state: FSMContext):
    # Проверяем, что состояние действительно confirm
    current_state = await state.get_state()
    if current_state != ReviewState.confirm:
        await callback.answer("❌ Неверное состояние", show_alert=True)
        return
    
    data = await state.get_data()
    
    # Еще раз проверяем наличие всех полей
    required_fields = ['photo', 'amount', 'currency', 'rating', 'text']
    if not all(field in data for field in required_fields):
        await callback.message.answer("❌ Ошибка: данные отзыва повреждены. Начните заново.")
        await state.clear()
        return
    
    try:
        async with aiosqlite.connect("database.db") as db:
            await db.execute(
                "INSERT INTO reviews(photo, amount, currency, rating, text) VALUES(?,?,?,?,?)",
                (
                    data["photo"],
                    data["amount"],
                    data["currency"],
                    int(data["rating"]),
                    data["text"]
                )
            )
            await db.commit()
        
        await callback.message.answer("✅ Отзыв успешно опубликован! Спасибо!")
        await state.clear()
        await callback.answer()
        
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка при сохранении: {e}")
        await state.clear()

@dp.callback_query(F.data == "cancel_review")
async def cancel_review(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("❌ Публикация отзыва отменена")
    await state.clear()
    await callback.answer()
# ================= SUPPORT =================

@dp.callback_query(F.data == "support")
async def support(callback: CallbackQuery, state: FSMContext):

    await callback.message.answer("💬 Напишите сообщение администрации")

    await state.set_state(SupportState.message)


@dp.message(SupportState.message)
async def send_support(message: Message, state: FSMContext):

    user = message.from_user

    async with aiosqlite.connect("database.db") as db:

        await db.execute(
            "INSERT INTO tickets(user_id,username,message) VALUES(?,?,?)",
            (user.id, user.username, message.text)
        )

        await db.commit()

    for admin in ADMIN_ID:

        kb = InlineKeyboardBuilder()

        kb.button(text="✉️ Ответить", callback_data=f"reply_{user.id}")
        kb.button(text="🔒 Закрыть тикет", callback_data=f"close_{user.id}")

        kb.adjust(1)

        await bot.send_message(
            admin,
            f"""
📨 Новый тикет

👤 @{user.username}
🆔 {user.id}

💬 {message.text}
""",
            reply_markup=kb.as_markup()
        )

    await message.answer("✅ Сообщение отправлено!")

    await state.clear()


# ================= ADMIN PANEL =================

@dp.message(Command("admin"))
async def admin_panel(message: Message):

    if message.from_user.id not in ADMIN_ID:
        return

    kb = InlineKeyboardBuilder()

    kb.button(text="⭐ Управление отзывами", callback_data="admin_reviews")
    kb.button(text="💬 Тикеты", callback_data="admin_tickets")

    kb.adjust(1)

    await message.answer("⚙️ Админ панель", reply_markup=kb.as_markup())


# ================= DELETE REVIEW =================

# ================= DELETE REVIEW =================

@dp.callback_query(F.data == "admin_reviews")
async def admin_reviews(callback: CallbackQuery):
    async with aiosqlite.connect("database.db") as db:
        async with db.execute("SELECT * FROM reviews") as cursor:
            rows = await cursor.fetchall()

    if not rows:
        await callback.message.answer("📭 Отзывов нет")
        return

    for r in rows:
        kb = InlineKeyboardBuilder()
        kb.button(text="🗑 Удалить", callback_data=f"del_{r[0]}")
        
        stars = "⭐" * r[4]  

        await callback.message.answer_photo(
            r[1],  # photo
            caption=f"""
⭐ Отзыв #{r[0]}

💰 Сумма: {r[2]} {r[3]}  
⭐ Рейтинг: {stars}

📝 {r[5]}
""",
            reply_markup=kb.as_markup()
        )

@dp.callback_query(F.data.startswith("del_"))
async def delete_review(callback: CallbackQuery):

    review_id = int(callback.data.split("_")[1])

    async with aiosqlite.connect("database.db") as db:

        await db.execute(
            "DELETE FROM reviews WHERE id=?",
            (review_id,)
        )

        await db.commit()

    await callback.message.answer("🗑 Отзыв удалён")

# ================= ADMIN TICKETS =================

# ================= ADMIN TICKETS =================

@dp.callback_query(F.data == "admin_tickets")
async def admin_tickets(callback: CallbackQuery):
    async with aiosqlite.connect("database.db") as db:
        async with db.execute("SELECT * FROM tickets ORDER BY id DESC") as cursor:
            tickets = await cursor.fetchall()
    
    if not tickets:
        await callback.message.answer("📭 Нет тикетов")
        return
    
    for ticket in tickets:
        kb = InlineKeyboardBuilder()
        kb.button(text="✉️ Ответить", callback_data=f"reply_{ticket[1]}")  # user_id на индексе 1
        kb.button(text="🔒 Закрыть", callback_data=f"close_{ticket[1]}")   # user_id на индексе 1
        kb.adjust(1)
        
        await callback.message.answer(
            f"""
📨 Тикет #{ticket[0]}  # id

👤 @{ticket[2]} (ID: {ticket[1]})  
💬 {ticket[3]}  

Выберите действие:
""",
            reply_markup=kb.as_markup()
        )
# ================= REPLY TO TICKET =================

@dp.callback_query(F.data.startswith("reply_"))
async def reply_to_ticket(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[1])
    await state.update_data(reply_to_user=user_id)
    await callback.message.answer("✉️ Введите ответ пользователю:")
    await state.set_state(SupportState.reply)

@dp.message(SupportState.reply)
async def send_reply(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("reply_to_user")
    
    try:
        await bot.send_message(
            user_id,
            f"✉️ Ответ от администрации:\n\n{message.text}"
        )
        await message.answer("✅ Ответ отправлен!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    
    await state.clear()
# ================= CLOSE TICKET =================

@dp.callback_query(F.data.startswith("close_"))
async def close_ticket(callback: CallbackQuery):

    user_id = int(callback.data.split("_")[1])

    async with aiosqlite.connect("database.db") as db:

        await db.execute(
            "DELETE FROM tickets WHERE user_id=?",
            (user_id,)
        )

        await db.commit()

    await callback.message.answer("🔒 Тикет закрыт")

# ================= GLOBAL CANCEL ON ANY COMMAND =================


@dp.message(Command(commands=["start", "admin", "cancel"]))  # Указываем конкретные команды
async def cancel_on_commands(message: Message, state: FSMContext):
    """Любая команда прерывает текущую операцию"""
    current_state = await state.get_state()
    
    if current_state is not None:
        await state.clear()
        # Отправляем уведомление об отмене
        await message.answer("✅ Текущая операция прервана из-за ввода команды")
    
    # Перенаправляем на соответствующий хендлер
    if message.text == "/start":
        await start(message)
    elif message.text == "/admin" and message.from_user.id in ADMIN_ID:
        await admin_panel(message)
    # /cancel обрабатывается отдельно

# ================= RUN =================

async def main():
    await init_db()
    print("🚀 BOT STARTED")
    
    # Запускаем с обработкой ошибок
    while True:
        try:
            await dp.start_polling(
                bot,
                polling_timeout=30,
                skip_updates=True
            )
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            print("🔄 Перезапуск через 5 секунд...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 BOT STOPPED")