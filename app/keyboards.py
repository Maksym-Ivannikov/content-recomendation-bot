from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def rec_type_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🎬 Фільм", callback_data="rec:type:movie"),
        InlineKeyboardButton(text="📺 Серіал", callback_data="rec:type:series"),
    ],[
        InlineKeyboardButton(text="📖 Книга", callback_data="rec:type:book"),
        InlineKeyboardButton(text="🎮 Гра",   callback_data="rec:type:game"),
    ]])

def categories_kb(prefix: str):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🎬 Фільми", callback_data=f"{prefix}:cat:movie"),
        InlineKeyboardButton(text="📺 Серіали", callback_data=f"{prefix}:cat:series"),
    ],[
        InlineKeyboardButton(text="📖 Книги",  callback_data=f"{prefix}:cat:book"),
        InlineKeyboardButton(text="🎮 Ігри",   callback_data=f"{prefix}:cat:game"),
    ]])

def abc_kb(prefix: str):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🅰 A", callback_data=f"{prefix}:A"),
        InlineKeyboardButton(text="🅱 B", callback_data=f"{prefix}:B"),
        InlineKeyboardButton(text="🇨 C", callback_data=f"{prefix}:C"),
    ]])

def approve_kb(qid: int):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Затвердити", callback_data=f"admin:approve:{qid}:1"),
        InlineKeyboardButton(text="❌ Відхилити",  callback_data=f"admin:approve:{qid}:0"),
    ],[
        InlineKeyboardButton(text="➡️ Наступне",   callback_data=f"admin:next")
    ]])
