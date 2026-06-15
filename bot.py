import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── КОНФИГ (задай через переменные окружения или впиши сюда) ───────────────
BOT_TOKEN     = os.getenv("BOT_TOKEN", "ВПИШИ_ТОКЕН_БОТА")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "ВПИШИ_СВОЙ_CHAT_ID")
# file_id PDF-гайда. Чтобы получить: отправь файл боту, бот сохранит id автоматически.
# Потом задай через /setpdf (см. команду ниже) или впиши сюда вручную.
PDF_FILE_ID   = os.getenv("PDF_FILE_ID", "")

# ─── СОСТОЯНИЯ РАЗГОВОРА ────────────────────────────────────────────────────
CHOOSING_SERVICE, DESCRIBING, CONFIRMING, ADDING_EXTRA = range(4)

# ─── ТЕКСТЫ ─────────────────────────────────────────────────────────────────
PRICES_TEXT = (
    "👉 <b>Iată ce primești când lucrezi cu Alexandru:</b>\n\n"
    "🔥 Montaj în stilul tău — ritm, culoare, tranziții\n"
    "🎨 Coloristică profesională\n"
    "🎵 Sound design îngrijit\n"
    "📁 Proiect complet livrat într-un folder ordonat\n"
    "⚡️ <b>Livrare în 2 zile</b>\n"
    "✏️ Runde de revizii incluse\n\n"
    "💵 <b>Prețuri:</b>\n"
    "— Highlight — de la <b>80€</b>\n"
    "— Film complet — de la <b>290€</b>\n"
    "— Love Story — de la <b>65€</b>\n"
    "— Reel — de la <b>45€</b>\n"
    "— Botez — de la <b>120€</b>\n\n"
    "<i>Toate prețurile includ TVA 15%</i>\n\n"
    "Ai un proiect diferit sau vrei o ofertă personalizată? Apasă 👇"
)

PORTFOLIO_TEXT = (
    "🎬 <b>Portofoliul meu:</b>\n\n"
    '📘 <a href="https://www.facebook.com/ciornii.videocreator">Facebook — Ciornii Videocreator</a>\n\n'
    "Aici găsești cele mai recente lucrări — highlight-uri, filme complete și reels."
)

MATERIAL_TEXT = (
    "🎁 <b>Ghid gratuit pentru tine!</b>\n\n"
    "Îți ofer un ghid practic care te va ajuta să-ți dezvolți afacerea online.\n\n"
    "📥 Descarcă-l mai jos 👇"
)

DESCRIBE_TEXTS = {
    "nunta": (
        "Descrie proiectul tău:\n\n"
        "📦 Volumul materialului (GB, dacă știi)\n"
        "⏱ Durata dorită:\n— Highlight\n— Film complet\n— Love Story\n"
        "📝 Orice altă informație relevantă\n\n"
        "Scrie tot într-un singur mesaj 👇"
    ),
    "botez": (
        "Descrie proiectul tău:\n\n"
        "📦 Volumul materialului (GB, dacă știi)\n"
        "⏱ Durata dorită a filmului\n"
        "📝 Orice altă informație relevantă\n\n"
        "Scrie tot într-un singur mesaj 👇"
    ),
    "reel": (
        "Descrie proiectul tău:\n\n"
        "📱 Câte reels ai nevoie?\n"
        "📝 Orice altă informație relevantă\n\n"
        "Scrie tot într-un singur mesaj 👇"
    ),
    "altceva": "Descrie pe scurt proiectul sau propunerea ta de colaborare 👇",
}

FINAL_TEXTS = {
    "nunta": (
        "Mulțumesc! Am notat tot și am trimis informațiile lui Alexandru. 📨\n\n"
        "👀 <b>Iată ce primești:</b>\n"
        "🔥 Montaj în stilul tău — ritm, culoare, tranziții\n"
        "🎨 Coloristică profesională\n"
        "🎵 Sound design îngrijit\n"
        "📁 Proiect complet livrat într-un folder ordonat\n"
        "⚡️ Livrare în 2 zile\n\n"
        "💵 <b>Prețuri:</b>\n"
        "— Highlight — de la <b>80€</b>\n"
        "— Film complet — de la <b>290€</b>\n"
        "— Love Story — de la <b>65€</b>\n"
        "— Reel — de la <b>45€</b>\n\n"
        "<i>Toate prețurile includ TVA 15%</i>\n\n"
        "Alexandru te va contacta în scurt timp. 🙌"
    ),
    "botez": (
        "Mulțumesc! Am notat tot și am trimis informațiile lui Alexandru. 📨\n\n"
        "👀 <b>Ce primești:</b>\n"
        "🔥 Montaj profesional în stilul tău\n"
        "🎨 Coloristică îngrijită\n"
        "🎵 Sound design + muzică\n"
        "✏️ 1 rundă de revizii inclusă\n"
        "⚡️ Livrare în 2 zile\n\n"
        "🕊 Botez (până la 7 min) — de la <b>120€</b>\n"
        "<i>Prețul include TVA 15%</i>\n\n"
        "Alexandru te va contacta în scurt timp. 🙌"
    ),
    "reel": (
        "Mulțumesc! Am notat tot și am trimis informațiile lui Alexandru. 📨\n\n"
        "👀 <b>Ce primești:</b>\n"
        "✅ Cele mai bune cadre selectate de mine\n"
        "✅ Coloristică profesională\n"
        "✅ Adaptat după referință, dacă ai una\n"
        "✅ Livrare în 2 zile\n"
        "✅ 1 rundă de revizii inclusă\n\n"
        "📱 Reel social media — de la <b>45€</b>\n"
        "<i>Prețul include TVA 15%</i>\n\n"
        "Alexandru te va contacta în scurt timp. 🙌"
    ),
    "altceva": (
        "Mulțumesc! Alexandru îți va scrie personal pentru a discuta proiectul "
        "și a-ți forma cea mai bună ofertă de pe piață. 🙌"
    ),
}

SERVICE_LABELS = {
    "nunta":   "💍 Nuntă",
    "botez":   "👶 Botez",
    "reel":    "📱 Reel social media",
    "altceva": "✏️ Altceva",
}

# ─── КЛАВИАТУРЫ ─────────────────────────────────────────────────────────────
def kb_main():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💵 Tarife",               callback_data="tarife")],
        [InlineKeyboardButton("🎬 Portofoliu",           callback_data="portofoliu")],
        [InlineKeyboardButton("📩 A comanda serviciul",  callback_data="comanda")],
        [InlineKeyboardButton("🎁 Material gratuit",     callback_data="material")],
    ])

def kb_service():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💍 Nuntă",            callback_data="nunta")],
        [InlineKeyboardButton("👶 Botez",             callback_data="botez")],
        [InlineKeyboardButton("📱 Reel social media", callback_data="reel")],
        [InlineKeyboardButton("✏️ Altceva",           callback_data="altceva")],
    ])

def kb_confirm():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Da, am scris tot",    callback_data="confirm_yes")],
        [InlineKeyboardButton("✏️ Vreau să adaug ceva", callback_data="confirm_add")],
    ])

def kb_after_order():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 A comanda serviciul", callback_data="comanda")],
        [InlineKeyboardButton("💵 Tarife",              callback_data="tarife")],
        [InlineKeyboardButton("🎬 Portofoliu",          callback_data="portofoliu")],
    ])

# ─── УВЕДОМЛЕНИЕ АДМИНИСТРАТОРУ ─────────────────────────────────────────────
async def notify_admin(bot, user, service: str, project: str, extra: str = ""):
    username = f"@{user.username}" if user.username else "—"
    name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "—"

    text = (
        "📥 <b>Новая заявка!</b>\n\n"
        f"👤 <b>Клиент:</b> {name}\n"
        f"📎 <b>Username:</b> {username}\n"
        f"🔗 <b>Написать:</b> <a href='tg://user?id={user.id}'>открыть чат</a>\n"
        f"📂 <b>Услуга:</b> {SERVICE_LABELS.get(service, service)}\n\n"
        f"📝 <b>Описание проекта:</b>\n{project}"
    )
    if extra:
        text += f"\n\n➕ <b>Дополнение:</b>\n{extra}"

    await bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=text,
        parse_mode="HTML",
    )

# ─── КОМАНДЫ ────────────────────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name or "prieten"
    await update.message.reply_text(
        f"Salut, {name}! 👋\n\n"
        "Sunt asistentul lui Alexandru — editor video pentru videografi de nunți și botezuri.\n\n"
        "Alege ce te interesează 👇",
        reply_markup=kb_main(),
    )

async def cmd_tarife(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(PRICES_TEXT, reply_markup=kb_after_order())

async def cmd_portofoliu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(PORTFOLIO_TEXT, reply_markup=kb_main())

async def cmd_contact(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(
        "🔗 <b>Contacte:</b>\n\n"
        '📘 <a href="https://www.facebook.com/ciornii.videocreator">Facebook</a>\n'
        '✈️ <a href="https://t.me/alexqabl">Telegram</a>'
    )

async def cmd_meniu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Vezi toate serviciile și opțiunile disponibile 👇",
        reply_markup=kb_main(),
    )

async def cmd_myid(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Помогает получить свой chat_id для настройки ADMIN_CHAT_ID."""
    await update.message.reply_text(f"Твой Chat ID: `{update.effective_user.id}`", parse_mode="Markdown")

async def cmd_setpdf(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Админ отправляет PDF файл с командой /setpdf — бот сохраняет file_id."""
    if str(update.effective_user.id) != str(ADMIN_CHAT_ID):
        return
    if update.message.document:
        file_id = update.message.document.file_id
        global PDF_FILE_ID
        PDF_FILE_ID = file_id
        await update.message.reply_text(
            f"✅ PDF сохранён!\n\nfile_id: `{file_id}`\n\n"
            "Скопируй это значение и задай как переменную окружения PDF_FILE_ID.",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text("Отправь PDF файл вместе с командой /setpdf")

# ─── ОБРАБОТЧИКИ CALLBACK (вне разговора) ───────────────────────────────────
async def cb_info(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Тарифы, портфолио, материал — не требуют состояния."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "tarife":
        await query.message.reply_html(PRICES_TEXT, reply_markup=kb_after_order())

    elif data == "portofoliu":
        await query.message.reply_html(
            PORTFOLIO_TEXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💵 Tarife",              callback_data="tarife")],
                [InlineKeyboardButton("📩 A comanda serviciul", callback_data="comanda")],
            ]),
        )

    elif data == "material":
        await query.message.reply_html(MATERIAL_TEXT, reply_markup=kb_after_order())
        if PDF_FILE_ID:
            await query.message.reply_document(PDF_FILE_ID)
        else:
            await query.message.reply_text("⚠️ Файл скоро будет доступен!")

# ─── РАЗГОВОР: ОФОРМЛЕНИЕ ЗАКАЗА ────────────────────────────────────────────
async def entry_comanda(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Точка входа: кнопка 'A comanda serviciul'."""
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Ce ai nevoie să montezi?", reply_markup=kb_service())
    return CHOOSING_SERVICE


async def choosing_service(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    service = query.data  # nunta / botez / reel / altceva
    ctx.user_data["service"] = service
    ctx.user_data["project"] = ""
    ctx.user_data["extra"] = ""
    await query.message.reply_text(DESCRIBE_TEXTS[service])
    return DESCRIBING


async def describing(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["project"] = update.message.text
    await update.message.reply_text(
        "Ai inclus tot ce era important? 😊",
        reply_markup=kb_confirm(),
    )
    return CONFIRMING


async def confirming_yes(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    service = ctx.user_data.get("service", "altceva")
    await query.message.reply_html(FINAL_TEXTS[service], reply_markup=kb_main())
    await notify_admin(
        ctx.bot,
        update.effective_user,
        service,
        ctx.user_data.get("project", "—"),
    )
    return ConversationHandler.END


async def confirming_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Adaugă ce lipsește 👇")
    return ADDING_EXTRA


async def adding_extra(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["extra"] = update.message.text
    service = ctx.user_data.get("service", "altceva")
    await update.message.reply_html(FINAL_TEXTS[service], reply_markup=kb_main())
    await notify_admin(
        ctx.bot,
        update.effective_user,
        service,
        ctx.user_data.get("project", "—"),
        ctx.user_data.get("extra", ""),
    )
    return ConversationHandler.END


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salut, {name}! 👋\n\nAlege ce te interesează 👇".format(
        name=update.effective_user.first_name or "prieten"
    ), reply_markup=kb_main())
    return ConversationHandler.END

# ─── ЗАПУСК БОТА ────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Команды
    app.add_handler(CommandHandler("start",      cmd_start))
    app.add_handler(CommandHandler("tarife",     cmd_tarife))
    app.add_handler(CommandHandler("portofoliu", cmd_portofoliu))
    app.add_handler(CommandHandler("contact",    cmd_contact))
    app.add_handler(CommandHandler("meniu",      cmd_meniu))
    app.add_handler(CommandHandler("myid",       cmd_myid))
    app.add_handler(MessageHandler(filters.Document.PDF & filters.Command("setpdf"), cmd_setpdf))

    # Разговор: оформление заказа
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(entry_comanda, pattern="^comanda$")],
        states={
            CHOOSING_SERVICE: [
                CallbackQueryHandler(choosing_service, pattern="^(nunta|botez|reel|altceva)$"),
            ],
            DESCRIBING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, describing),
            ],
            CONFIRMING: [
                CallbackQueryHandler(confirming_yes, pattern="^confirm_yes$"),
                CallbackQueryHandler(confirming_add, pattern="^confirm_add$"),
            ],
            ADDING_EXTRA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, adding_extra),
            ],
        },
        fallbacks=[CommandHandler("start", cancel)],
        per_chat=True,
    )
    app.add_handler(conv)

    # Информационные кнопки (тарифы, портфолио, материал)
    app.add_handler(CallbackQueryHandler(cb_info, pattern="^(tarife|portofoliu|material)$"))

    logger.info("Бот запущен...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
