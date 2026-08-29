import asyncio
import json
import logging
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiohttp import web
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
PORT = int(os.getenv("PORT", "10000"))  # Render bu o'zgaruvchini o'zi beradi

# ==== O'ZGARTIRISHINGIZ MUMKIN BO'LGAN QISM ====
WEBSITE_URL = "https://1myblog.netlify.app/"
CHANNEL_URL = "https://t.me/+UCpfGMn2R3Y2NmU6"
SECOND_BOT_URL = "https://t.me/YashirinAloqaBot"
MINI_GAME_URL = "https://kichik-oyin.netlify.app/"
PORTFOLIO_URL = "https://portfolyu2026.netlify.app/"
APP_DATA_FILE = "app_file.json"  # admin yuborgan ilova fayli shu yerda saqlanadi
# =================================================

logging.basicConfig(level=logging.INFO)
router = Router()


def save_app_file(file_id: str, file_name: str = "", file_type: str = "document"):
    with open(APP_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"file_id": file_id, "file_name": file_name, "file_type": file_type}, f)


def load_app_file():
    if os.path.exists(APP_DATA_FILE):
        with open(APP_DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    return None


def delete_app_file():
    if os.path.exists(APP_DATA_FILE):
        os.remove(APP_DATA_FILE)
        return True
    return False


WELCOME_TEXT = (
    "Assalomu alaykum! 👋\n\n"
    "Bu bot — yo'naltiruvchi bot hisoblanadi.\n\n"
    "🌐 <b>Shaxsiy veb-saytim</b>\n"
    "Bu yerda o'zimga yoqqan va foydali deb bilgan kontentlarni ulashib boraman.\n"
    "• 🎥 YouTube\n"
    "• 📸 Instagram\n"
    "• 🖼 Rasmlar\n"
    "• 🎵 Qo'shiqlar\n"
    "• 📚 Foydali manbalar\n\n"
    "💻 <b>CodeVersePY</b>\n"
    "Ushbu kanalda turli xil tayyor Telegram bot kodlari va Python loyihalari ulashib boriladi.\n"
    "✅ Tayyor bot kodlari\n"
    "✅ Ochiq manbali (Open Source) loyihalar\n"
    "✅ Bepul foydalanish mumkin\n"
    "✅ Yuklab olib darhol ishga tushirish mumkin\n\n"
    "🤖 <b>Yashirin Aloqa Bot</b>\n"

    
    "Quyidagi tugmalardan birini tanlang 👇"
)


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌐 Saytga kirish", url=WEBSITE_URL)],
            [InlineKeyboardButton(text="💻 Kanalga kirish", url=CHANNEL_URL)],
            [InlineKeyboardButton(text="🤖 Botga kirish", url=SECOND_BOT_URL)],
            [InlineKeyboardButton(text="📥 Web ilovasini yuklash", callback_data="get_app")],
            [InlineKeyboardButton(text="🧑‍💻 Portfolyo", url=PORTFOLIO_URL)],
        ]
    )


def admin_file_kb(has_file: bool) -> InlineKeyboardMarkup:
    """Admin uchun joriy fayl holatiga qarab boshqaruv tugmalari."""
    if has_file:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🗑 Faylni o'chirish", callback_data="delete_app_file")]
            ]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Holatni yangilash", callback_data="check_app_file")]
        ]
    )


def user_info_text(message: Message) -> str:
    user = message.from_user
    return (
        "🆕 <b>Yangi foydalanuvchi /start bosdi</b>\n\n"
        f"👤 Ism: {user.full_name}\n"
        f"🔗 Username: @{user.username if user.username else '—'}\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"🕒 Vaqt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())

    if ADMIN_ID:
        try:
            await bot.send_message(ADMIN_ID, user_info_text(message))
        except Exception as e:
            logging.warning(f"Adminga xabar yuborilmadi: {e}")


@router.callback_query(F.data == "get_app")
async def send_app(callback: CallbackQuery, bot: Bot):
    app = load_app_file()
    if app and app.get("file_id"):
        await bot.send_document(
            callback.from_user.id,
            app["file_id"],
            caption="📥 Ilova tayyor! Yuklab oling.",
        )
    else:
        await callback.message.answer(
            "⚠️ Hozircha ilova fayli yuklanmagan. Tez orada qo'shiladi."
        )
    await callback.answer()


@router.message(Command("fayl"), F.from_user.id == ADMIN_ID)
async def cmd_admin_file(message: Message):
    """Admin joriy yuklangan faylni va uni o'chirish tugmasini ko'radi."""
    app = load_app_file()
    if app:
        text = f"📄 Hozirgi fayl: <b>{app.get('file_name') or 'nomsiz fayl'}</b>"
    else:
        text = "⚠️ Hozircha hech qanday fayl yuklanmagan."
    await message.answer(text, reply_markup=admin_file_kb(bool(app)))


@router.callback_query(F.data == "delete_app_file", F.from_user.id == ADMIN_ID)
async def cb_delete_app_file(callback: CallbackQuery):
    deleted = delete_app_file()
    if deleted:
        await callback.message.edit_text(
            "✅ Fayl muvaffaqiyatli o'chirildi. Endi foydalanuvchilarga fayl yuborilmaydi.",
            reply_markup=admin_file_kb(False),
        )
    else:
        await callback.message.edit_text(
            "⚠️ O'chiradigan fayl topilmadi.",
            reply_markup=admin_file_kb(False),
        )
    await callback.answer("O'chirildi" if deleted else "Fayl yo'q edi")


@router.callback_query(F.data == "check_app_file", F.from_user.id == ADMIN_ID)
async def cb_check_app_file(callback: CallbackQuery):
    app = load_app_file()
    if app:
        text = f"📄 Hozirgi fayl: <b>{app.get('file_name') or 'nomsiz fayl'}</b>"
    else:
        text = "⚠️ Hozircha hech qanday fayl yuklanmagan."
    await callback.message.edit_text(text, reply_markup=admin_file_kb(bool(app)))
    await callback.answer()


@router.message(F.from_user.id == ADMIN_ID, F.document)
async def admin_upload_app(message: Message):
    """Admin botga fayl (apk, zip va h.k.) yuborsa, avtomatik ilova sifatida saqlanadi."""
    save_app_file(message.document.file_id, message.document.file_name or "")
    await message.answer(
        f"✅ Ilova saqlandi: <b>{message.document.file_name or 'nomsiz fayl'}</b>\n"
        "Endi foydalanuvchilar '📥 Web ilovasini yuklash' tugmasini bossa, shu fayl ularga yuboriladi.",
        reply_markup=admin_file_kb(True),
    )


@router.message()
async def forward_to_admin(message: Message, bot: Bot):
    """Foydalanuvchi yuborgan har qanday xabarni (matn, rasm, video, fayl va h.k.)
    adminga kimligi bilan birga yetkazadi."""
    if not ADMIN_ID or (message.from_user and message.from_user.id == ADMIN_ID):
        return

    user = message.from_user
    caption = (
        "✉️ <b>Yangi xabar</b>\n"
        f"👤 {user.full_name} (@{user.username or '—'})\n"
        f"🆔 <code>{user.id}</code>\n"
        "────────────"
    )
    try:
        await bot.send_message(ADMIN_ID, caption)
        await bot.copy_message(
            chat_id=ADMIN_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
        )
    except Exception as e:
        logging.warning(f"Xabar forward qilinmadi: {e}")


async def healthz(request: web.Request) -> web.Response:
    """UptimeRobot shu manzilga ping tashlab, Render'ni uxlab qolishdan saqlaydi."""
    return web.Response(text="OK")


async def start_web_server():
    """Render'ning bepul Web Service'i ishlashi uchun kichik HTTP server.
    Render web-servisga port ochilishini talab qiladi, aks holda deploy muvaffaqiyatsiz bo'ladi."""
    app = web.Application()
    app.router.add_get("/", healthz)
    app.router.add_get("/healthz", healthz)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=PORT)
    await site.start()
    logging.info(f"HTTP server {PORT}-portda ishga tushdi (keep-alive uchun)")


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN topilmadi. .env faylini tekshiring.")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)

    # HTTP server va botni bir vaqtda ishga tushiramiz
    await start_web_server()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
