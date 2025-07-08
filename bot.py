import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.markdown import hbold

API_TOKEN = '7994840465:AAFKcaG62VZQzUZ7n0FYOR4YqHEK2cJnjr0'
ADMIN_ID = 947000812

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

user_messages = {}
active_users = set()
last_bot_message = {}
last_bot_gif_message = {}
last_warning_message = {}
admin_reply_context = {}

start_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Послать весть", callback_data="send_message")]
])

send_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Отправить", callback_data="final_send")]
])

cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Отменить", callback_data="go_back")]
])

back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Вернуться назад", callback_data="go_back")]
])


def admin_notification_keyboard(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ответить", callback_data=f"reply_to_{user_id}")]
    ])


async def send_welcome_message(chat_id: int):
    # Сначала отправляем гифку и сохраняем её ID
    gif = await bot.send_animation(chat_id, animation="https://media1.tenor.com/m/T0K86nFmVfQAAAAC/welcome-youre-welcome.gif")
    last_bot_gif_message[chat_id] = gif.message_id

    text = (
        "Иногда самые важные слова находят путь к адресату не сразу, а через верных посредников. "
        "Вы сейчас беседуете с таким — моим личным ботом.\n\n"
        "Просто нажмите кнопку внизу, чтобы отправить мне свои сообщения. Я прочту, откликнусь, "
        "а если нужно — соединю вас с собой напрямую."
    )
    sent = await bot.send_message(chat_id, text, reply_markup=start_keyboard)
    last_bot_message[chat_id] = sent.message_id


@dp.message()
async def handle_any_message(message: types.Message):
    user_id = message.from_user.id

    if user_id == ADMIN_ID and user_id in admin_reply_context:
        admin_reply_context[user_id]['messages'].append(message)
        return

    if user_id not in active_users:
        active_users.add(user_id)
        await send_welcome_message(user_id)
        return

    if user_id in user_messages:
        user_messages[user_id].append(message)

        if user_id in last_warning_message:
            try:
                await bot.delete_message(chat_id=user_id, message_id=last_warning_message[user_id])
            except:
                pass
            del last_warning_message[user_id]


@dp.callback_query(F.data == "send_message")
async def send_message_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_messages[user_id] = []

    # Удаляем предыдущие сообщения и гифки
    if user_id in last_bot_message:
        try:
            await bot.delete_message(chat_id=user_id, message_id=last_bot_message[user_id])
        except:
            pass

    if user_id in last_bot_gif_message:
        try:
            await bot.delete_message(chat_id=user_id, message_id=last_bot_gif_message[user_id])
        except:
            pass

    # Отправляем гифку перед сообщением с кнопкой "Отправить"
    gif = await callback.message.answer_animation("https://media1.tenor.com/m/ulcWD1uF7vMAAAAC/anime-keyboard.gif")
    last_bot_gif_message[user_id] = gif.message_id

    sent = await callback.message.answer(
        "Оставьте свои сообщения и они непременно дойдут до меня!!\n\n"
        "После того как всё необходимое будет написано, обязательно нажмите кнопку «Отправить».",
        reply_markup=send_keyboard
    )
    last_bot_message[user_id] = sent.message_id


@dp.callback_query(F.data == "final_send")
async def final_send_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    msgs = user_messages.get(user_id)

    if user_id in last_warning_message:
        try:
            await bot.delete_message(chat_id=user_id, message_id=last_warning_message[user_id])
        except:
            pass
        del last_warning_message[user_id]

    if not msgs or len(msgs) == 0:
        warning = await callback.message.answer(
            "Вы ничего не отправили. Пожалуйста, убедитесь, что перед нажатием кнопки «Отправить» сообщение действительно было написано.",
            reply_markup=cancel_keyboard
        )
        last_warning_message[user_id] = warning.message_id
        return

    # Удаляем предыдущие сообщения и гифки
    if user_id in last_bot_message:
        try:
            await bot.delete_message(chat_id=user_id, message_id=last_bot_message[user_id])
        except:
            pass

    if user_id in last_bot_gif_message:
        try:
            await bot.delete_message(chat_id=user_id, message_id=last_bot_gif_message[user_id])
        except:
            pass

    username = f"@{callback.from_user.username}" if callback.from_user.username else "(нет username)"
    header = (
        f"📨 Новое сообщение от <b>{hbold(callback.from_user.full_name)}</b>\n"
        f"🔹 Username: {username}\n"
        f"🔹 ID: <code>{user_id}</code>\n\n"
    )

    await bot.send_message(ADMIN_ID, header, reply_markup=admin_notification_keyboard(user_id))
    for msg in msgs:
        try:
            await msg.copy_to(ADMIN_ID)
        except Exception as e:
            logging.error(f"Ошибка при пересылке: {e}")

    user_messages[user_id] = []

    # Отправляем гифку перед сообщением "Ваши сообщения успешно доставлены..."
    gif = await bot.send_animation(
        user_id,
        animation="https://media1.tenor.com/m/KxCdhyI1Dl4AAAAC/baby-cute.gif"
    )
    last_bot_gif_message[user_id] = gif.message_id

    sent = await bot.send_message(
        user_id,
        "Ваши сообщения успешно доставлены.\n"
        "Как только у меня появится возможность — я обязательно их прочту и отвечу Вам.\n\n"
        "Пожалуйста, не отправляйте новых сообщений повторно не убедившись в том, что проделали те же самые манипуляции, что и раньше, вернитесь назад. "
        "Если захотите что-то дополнить или изменить — просто отредактируйте свои предыдущее сообщения.",
        reply_markup=back_keyboard
    )
    last_bot_message[user_id] = sent.message_id


@dp.callback_query(F.data.startswith("reply_to_"))
async def admin_reply_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer("У вас нет прав отвечать.")
        return

    target_user_id = int(callback.data.split("_")[-1])
    admin_reply_context[user_id] = {
        'user_id': target_user_id,
        'messages': []
    }

    await callback.message.answer(
        f"Вы начали отвечать пользователю с ID <b>{target_user_id}</b>.\n"
        "Пишите свои сообщения. Когда закончите — нажмите кнопку «Отправить».",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Отправить", callback_data="admin_final_send")],
            [InlineKeyboardButton(text="Отменить", callback_data="admin_cancel_reply")]
        ])
    )
    await callback.answer()


@dp.callback_query(F.data == "admin_final_send")
async def admin_final_send_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id != ADMIN_ID or user_id not in admin_reply_context:
        await callback.answer("Нет активного диалога для отправки.")
        return

    context = admin_reply_context[user_id]
    target_user_id = context['user_id']
    messages_to_send = context['messages']

    if not messages_to_send:
        await callback.message.answer("Вы не написали ни одного сообщения.")
        return

    for msg in messages_to_send:
        try:
            await msg.copy_to(target_user_id)
        except Exception as e:
            logging.error(f"Ошибка при отправке пользователю: {e}")

    await callback.message.answer("Сообщения отправлены пользователю.", reply_markup=back_keyboard)
    del admin_reply_context[user_id]


@dp.callback_query(F.data == "admin_cancel_reply")
async def admin_cancel_reply_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id == ADMIN_ID and user_id in admin_reply_context:
        del admin_reply_context[user_id]

    await callback.message.answer("Ответ отменён.", reply_markup=back_keyboard)


@dp.callback_query(F.data == "go_back")
async def go_back_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    # Удаляем предупреждение, если есть
    if user_id in last_warning_message:
        try:
            await bot.delete_message(chat_id=user_id, message_id=last_warning_message[user_id])
        except:
            pass
        del last_warning_message[user_id]

    # Удаляем последнее бот-сообщение
    if user_id in last_bot_message:
        try:
            await bot.delete_message(chat_id=user_id, message_id=last_bot_message[user_id])
        except:
            pass

    # Удаляем гифку, связанную с последним бот-сообщением
    if user_id in last_bot_gif_message:
        try:
            await bot.delete_message(chat_id=user_id, message_id=last_bot_gif_message[user_id])
        except:
            pass

    # НЕ удаляем сообщения пользователя

    await send_welcome_message(user_id)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
