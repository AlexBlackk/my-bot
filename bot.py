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
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "2074001393")  # Alex C. (@ACiornii)

# ─── СОСТОЯНИЯ РАЗГОВОРА ────────────────────────────────────────────────────
(
    STARTED,
    Q1, Q1_CUSTOM,
    Q2, Q2_CUSTOM,
    Q3, Q3_CUSTOM,
    MENU,
    CHOOSING_SERVICE, DESCRIBING, CONFIRMING, ADDING_EXTRA,
) = range(12)

# ─── КВАЛИФИКАЦИЯ (3 вопроса) ───────────────────────────────────────────────
QUIZ = {
    "q1": {
        "text": "Câte nunți filmezi anual?",
        "options": ["5–10 nunți", "10–20 nunți", "Peste 20 de nunți"],
    },
    "q2": {
        "text": "De ce cauți un editor extern?",
        "options": [
            "Nu mai am timp pentru montaj",
            "Vreau să iau mai multe proiecte",
            "Caut o soluție mai accesibilă",
            "Nu vreau să mai montez singur",
        ],
    },
    "q3": {
        "text": "Ce este cel mai important pentru tine?",
        "options": ["Preț", "Viteză", "Calitate", "Stabilitate", "Colaborare pe termen lung"],
    },
}

CUSTOM_PROMPT = "Scrie varianta ta într-un singur mesaj 👇"

# ─── ТЕКСТЫ ─────────────────────────────────────────────────────────────────
START_TEXT = (
    "Salut! 👋\n\n"
    "Sunt asistentul editorului tău video.\n\n"
    "Îți voi pune 3 întrebări rapide. Durează aproximativ 30 de secunde."
)

MENU_TEXT = (
    "Mulțumesc! Am notat răspunsurile tale.\n\n"
    "Acum poți vedea prețurile, portofoliul sau poți comanda montajul."
)

PRICES_TEXT = (
    "<b>Alege pachetul potrivit</b>\n\n"
    "Prețurile sunt orientative. Îți pregătim o ofertă individuală, adaptată "
    "proiectului tău — trebuie doar să ne contactezi.\n\n"
    "🔥 Montaj în stilul tău — ritm, culoare, tranziții\n"
    "🎨 Color grading\n"
    "🎵 Sound design\n"
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
    '🌐 <a href="https://editorultau.com/portofoliu.dc">Vezi portofoliul</a>'
)

CONTACT_TEXT = (
    "🔗 <b>Contacte:</b>\n\n"
    '📘 <a href="https://www.facebook.com/ciornii.videocreator">Facebook</a>\n'
    '✈️ <a href="https://t.me/alexqabl">Telegram</a>\n'
    '🟢 <a href="https://wa.me/37379840751">WhatsApp</a>'
)

DESCRIBE_TEXTS = {
    "nunta": (
        "Descrie proiectul tău:\n\n"
        "📦 Volumul materialului (GB, dacă știi)\n"
        "⏱ Durata dorită:\n— Highlight\n— Film complet\n— Love Story\n"
        "📝 Orice altă informație relevantă\n\n"
        "📞 Obligatoriu: lasă numărul tău de telefon sau un alt contact prin care "
        "te pot contacta. De preferat — numărul de telefon.\n\n"
        "Scrie tot într-un singur mesaj 👇"
    ),
    "botez": (
        "Descrie proiectul tău:\n\n"
        "📦 Volumul materialului (GB, dacă știi)\n"
        "⏱ Durata dorită a filmului\n"
        "📝 Orice altă informație relevantă\n\n"
        "📞 Obligatoriu: lasă numărul tău de telefon sau un alt contact prin care "
        "te pot contacta. De preferat — numărul de telefon.\n\n"
        "Scrie tot într-un singur mesaj 👇"
    ),
    "reel": (
        "Descrie proiectul tău:\n\n"
        "📱 Câte reels ai nevoie?\n"
        "📝 Orice altă informație relevantă\n\n"
        "📞 Obligatoriu: lasă numărul tău de telefon sau un alt contact prin care "
        "te pot contacta. De preferat — numărul de telefon.\n\n"
        "Scrie tot într-un singur mesaj 👇"
    ),
    "altceva": (
        "Descrie pe scurt proiectul sau propunerea ta de colaborare.\n\n"
        "📞 Obligatoriu: lasă numărul tău de telefon sau un alt contact prin care "
        "te pot contacta. De preferat — numărul de telefon.\n\n"
        "Scrie tot într-un singur mesaj 👇"
    ),
}

FINAL_TEXT = (
    "Mulțumesc! Cererea ta a fost primită. 📨\n\n"
    "Prețul final va fi adaptat individual, în funcție de proiectul tău."
)

SERVICE_LABELS = {
    "nunta":   "💍 Nuntă",
    "botez":   "👶 Botez",
    "reel":    "📱 Reel social media",
    "altceva": "✏️ Altceva",
}

# ─── КЛАВИАТУРЫ ─────────────────────────────────────────────────────────────
def kb_continue():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Continuăm", callback_data="continua")],
    ])

def kb_quiz(qkey):
    rows = [
        [InlineKeyboardButton(opt, callback_data=f"{qkey}_{i}")]
        for i, opt in enumerate(QUIZ[qkey]["options"])
    ]
    rows.append([InlineKeyboardButton("✏️ Varianta mea", callback_data=f"{qkey}_custom")])
    return InlineKeyboardMarkup(rows)

def kb_main():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💵 Tarife",              callback_data="tarife")],
        [InlineKeyboardButton("🎬 Portofoliu",          callback_data="portofoliu")],
        [InlineKeyboardButton("📩 A comanda serviciul", callback_data="comanda")],
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
async def notify_admin(bot, user, ctx, service: str, project: str, extra: str = ""):
    username = f"@{user.username}" if user.username else "—"
    name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "—"

    q1 = ctx.user_data.get("q1", "—")
    q2 = ctx.user_data.get("q2", "—")
    q3 = ctx.user_data.get("q3", "—")

    text = (
        "📥 <b>Новая заявка!</b>\n\n"
        f"👤 <b>Клиент:</b> {name}\n"
        f"📎 <b>Username:</b> {username}\n"
        f"🔗 <b>Написать:</b> <a href='tg://user?id={user.id}'>открыть чат</a>\n"
        f"📂 <b>Услуга:</b> {SERVICE_LABELS.get(service, service)}\n\n"
        "📊 <b>Квалификация:</b>\n"
        f"• Свадеб в год: {q1}\n"
        f"• Зачем внешний монтажёр: {q2}\n"
        f"• Что важнее всего: {q3}\n\n"
        f"📝 <b>Описание проекта:</b>\n{project}"
    )
    if extra:
        text += f"\n\n➕ <b>Дополнение:</b>\n{extra}"

    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=text, parse_mode="HTML")

# ─── РАЗГОВОР: START → КВАЛИФИКАЦИЯ → МЕНЮ → ЗАКАЗ ──────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(START_TEXT, reply_markup=kb_continue())
    return STARTED


async def on_continua(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(QUIZ["q1"]["text"], reply_markup=kb_quiz("q1"))
    return Q1


# ── Вопрос 1 ──
async def q1_answer(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = int(query.data.split("_")[1])
    ctx.user_data["q1"] = QUIZ["q1"]["options"][idx]
    await query.message.reply_text(QUIZ["q2"]["text"], reply_markup=kb_quiz("q2"))
    return Q2

async def q1_custom_prompt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(CUSTOM_PROMPT)
    return Q1_CUSTOM

async def q1_custom_save(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["q1"] = update.message.text
    await update.message.reply_text(QUIZ["q2"]["text"], reply_markup=kb_quiz("q2"))
    return Q2


# ── Вопрос 2 ──
async def q2_answer(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = int(query.data.split("_")[1])
    ctx.user_data["q2"] = QUIZ["q2"]["options"][idx]
    await query.message.reply_text(QUIZ["q3"]["text"], reply_markup=kb_quiz("q3"))
    return Q3

async def q2_custom_prompt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(CUSTOM_PROMPT)
    return Q2_CUSTOM

async def q2_custom_save(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["q2"] = update.message.text
    await update.message.reply_text(QUIZ["q3"]["text"], reply_markup=kb_quiz("q3"))
    return Q3


# ── Вопрос 3 → меню ──
async def q3_answer(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = int(query.data.split("_")[1])
    ctx.user_data["q3"] = QUIZ["q3"]["options"][idx]
    await query.message.reply_text(MENU_TEXT, reply_markup=kb_main())
    return MENU

async def q3_custom_prompt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(CUSTOM_PROMPT)
    return Q3_CUSTOM

async def q3_custom_save(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["q3"] = update.message.text
    await update.message.reply_text(MENU_TEXT, reply_markup=kb_main())
    return MENU


# ── Заказ ──
async def entry_comanda(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
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
    await query.message.reply_html(FINAL_TEXT, reply_markup=kb_main())
    await notify_admin(
        ctx.bot, update.effective_user, ctx,
        service, ctx.user_data.get("project", "—"),
    )
    return MENU


async def confirming_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Adaugă ce lipsește 👇")
    return ADDING_EXTRA


async def adding_extra(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["extra"] = update.message.text
    service = ctx.user_data.get("service", "altceva")
    await update.message.reply_html(FINAL_TEXT, reply_markup=kb_main())
    await notify_admin(
        ctx.bot, update.effective_user, ctx,
        service, ctx.user_data.get("project", "—"), ctx.user_data.get("extra", ""),
    )
    return MENU


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(START_TEXT, reply_markup=kb_continue())
    return STARTED

# ─── КОМАНДЫ (вне разговора) ────────────────────────────────────────────────
async def cmd_tarife(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(PRICES_TEXT, reply_markup=kb_after_order())

async def cmd_portofoliu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(PORTFOLIO_TEXT, reply_markup=kb_main())

async def cmd_contact(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(CONTACT_TEXT)

async def cmd_meniu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Vezi toate serviciile și opțiunile disponibile 👇",
        reply_markup=kb_main(),
    )

async def cmd_myid(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Помогает получить свой chat_id для настройки ADMIN_CHAT_ID."""
    await update.message.reply_text(
        f"Твой Chat ID: `{update.effective_user.id}`", parse_mode="Markdown"
    )

# ─── ИНФО-КНОПКИ (вне разговора: тарифы, портфолио) ─────────────────────────
async def cb_info(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
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

# ─── ЗАПУСК БОТА ────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Единый разговор: /start → квалификация → меню → заказ
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", cmd_start),
            CallbackQueryHandler(entry_comanda, pattern="^comanda$"),
        ],
        states={
            STARTED: [
                CallbackQueryHandler(on_continua, pattern="^continua$"),
            ],
            Q1: [
                CallbackQueryHandler(q1_custom_prompt, pattern="^q1_custom$"),
                CallbackQueryHandler(q1_answer, pattern=r"^q1_\d+$"),
            ],
            Q1_CUSTOM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, q1_custom_save),
            ],
            Q2: [
                CallbackQueryHandler(q2_custom_prompt, pattern="^q2_custom$"),
                CallbackQueryHandler(q2_answer, pattern=r"^q2_\d+$"),
            ],
            Q2_CUSTOM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, q2_custom_save),
            ],
            Q3: [
                CallbackQueryHandler(q3_custom_prompt, pattern="^q3_custom$"),
                CallbackQueryHandler(q3_answer, pattern=r"^q3_\d+$"),
            ],
            Q3_CUSTOM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, q3_custom_save),
            ],
            MENU: [
                CallbackQueryHandler(entry_comanda, pattern="^comanda$"),
            ],
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
        allow_reentry=True,
    )
    app.add_handler(conv)

    # Команды
    app.add_handler(CommandHandler("tarife",     cmd_tarife))
    app.add_handler(CommandHandler("portofoliu", cmd_portofoliu))
    app.add_handler(CommandHandler("contact",    cmd_contact))
    app.add_handler(CommandHandler("meniu",      cmd_meniu))
    app.add_handler(CommandHandler("myid",       cmd_myid))

    # Инфо-кнопки (тарифы, портфолио) — работают вне разговора
    app.add_handler(CallbackQueryHandler(cb_info, pattern="^(tarife|portofoliu)$"))

    logger.info("Бот запущен...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
