import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

BOT_TOKEN = "8960595836:AAF-9JLDFxYYZceo_0R-q0aulPZR429Cm8A"

channels_list = ["@shevchikpatrul"]
active_channel = "@shevchikpatrul"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

class PostStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_confirmation = State()

THREAT_TYPES = {
    "kab_threat": "⚠️ Загроза КАБ",
    "kab_launch": "💥 Пуск КАБ",
    "planes_pu": "🛩 Куди літаки на ПУ",
    "bal_threat": "⚡ Загроза балістики",
    "shahed_threat": "🚨 Загроза Шахедів / Гераней",
    "alert_yellow": "🟡 Тривога (Жовтий)",
    "alert_red": "🔴 Тривога (Червоний)",
    "cruise_missile": "🚀 Загроза крилатих ракет",
    "fast_target": "⚡ Загроза високошвидкісних цілей",
    "fpv_threat": "🛸 Загроза FPV"
}

def get_channels_keyboard():
    buttons = []
    for ch in channels_list:
        prefix = "✅ " if ch == active_channel else "📢 "
        buttons.append([InlineKeyboardButton(text=f"{prefix}{ch}", callback_data=f"select_chan_{ch}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_location_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏢 м. Запоріжжя", callback_data="loc_city")],
        [InlineKeyboardButton(text="🌾 Запорізька область", callback_data="loc_region")]
    ])

def get_threats_keyboard():
    buttons = [[InlineKeyboardButton(text=v, callback_data=f"threat_{k}")] for k, v in THREAT_TYPES.items()]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Опублікувати в канал", callback_data="send_to_channel")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_post")]
    ])

@dp.message(Command("channels"))
async def cmd_channels(message: types.Message):
    await message.answer(
        f"📢 **Управління каналами**\n\n"
        f"Поточний активний канал: `{active_channel}`\n\n"
        f"Оберіть канал зі списку, щоб зробити його активним:\n"
        f"• Додати новий: `/addchannel @имя_канала`\n"
        f"• Видалити канал: `/delchannel @имя_канала`",
        reply_markup=get_channels_keyboard(),
        parse_mode="Markdown"
    )

@dp.message(Command("addchannel"))
async def cmd_add_channel(message: types.Message):
    global active_channel
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️️ Вкажіть назву канала:\n`/addchannel @my_channel`", parse_mode="Markdown")
        return
    new_ch = args[1].strip()
    if new_ch not in channels_list:
        channels_list.append(new_ch)
        active_channel = new_ch
        await message.answer(f"✅ Канал `{new_ch}` додано та обрано як активний!", parse_mode="Markdown")
    else:
        await message.answer(f"ℹ️ Канал `{new_ch}` вже є у списку.", parse_mode="Markdown")

@dp.message(Command("delchannel"))
async def cmd_del_channel(message: types.Message):
    global active_channel
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ Вкажіть назву канала:\n`/delchannel @my_channel`", parse_mode="Markdown")
        return
    ch_to_del = args[1].strip()
    if ch_to_del in channels_list:
        channels_list.remove(ch_to_del)
        if active_channel == ch_to_del:
            active_channel = channels_list[0] if channels_list else "Не обрано"
        await message.answer(f"❌ Канал `{ch_to_del}` видалено зі списку!", parse_mode="Markdown")
    else:
        await message.answer(f"ℹ️ Канал `{ch_to_del}` не знайдено.", parse_mode="Markdown")

@dp.callback_query(F.data.startswith("select_chan_"))
async def process_select_channel(callback: types.CallbackQuery):
    global active_channel
    selected_ch = callback.data.replace("select_chan_", "")
    active_channel = selected_ch
    await callback.message.edit_text(
        f"✅ **Активний канал змінено на:** `{active_channel}`\n\n"
        f"Тепер усі дописи надсилатимуться сюди. Введіть /start для публікації.",
        reply_markup=get_channels_keyboard(),
        parse_mode="Markdown"
    )

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"🚨 **Бот моніторингу загроз (Запоріжжя / Область)**\n"
        f"📢 Допис буде надіслано в: `{active_channel}`\n"
        f"*(Щоб змінити канал, введіть /channels)*\n\n"
        "Оберіть локацію:",
        reply_markup=get_location_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("loc_"))
async def process_location(callback: types.CallbackQuery, state: FSMContext):
    loc_text = "🏢 м. Запоріжжя" if callback.data == "loc_city" else "🌾 Запорізька область"
    await state.update_data(location=loc_text)
    await callback.message.edit_text(
        f"Локація: **{loc_text}**\n\nТепер оберіть тип загрози:",
        reply_markup=get_threats_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("threat_"))
async def process_threat(callback: types.CallbackQuery, state: FSMContext):
    threat_key = callback.data.replace("threat_", "")
    threat_name = THREAT_TYPES[threat_key]
    await state.update_data(threat=threat_name)
    await state.set_state(PostStates.waiting_for_text)
    data = await state.get_data()
    await callback.message.edit_text(
        f"📍 Локація: **{data.get('location')}**\n"
        f"🚨 Загроза: **{threat_name}**\n\n"
        "✍️ **Напишіть текст повідомлення для цього допису з нуля:**",
        parse_mode="Markdown"
    )

@dp.message(PostStates.waiting_for_text)
async def process_custom_text(message: types.Message, state: FSMContext):
    await state.update_data(post_text=message.text)
    await state.set_state(PostStates.waiting_for_confirmation)
    data = await state.get_data()
    preview = f"📍 **{data.get('location')}**\n🚨 **{data.get('threat')}**\n\n{message.text}"
    await message.answer(
        f"🔍 **Попередній перегляд (Канал: {active_channel}):**\n"
        "-------------------------------\n"
        f"{preview}\n"
        "-------------------------------\n"
        "Опублікувати в канал?",
        reply_markup=get_confirm_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "send_to_channel", PostStates.waiting_for_confirmation)
async def send_post(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    final_post = f"📍 **{data.get('location')}**\n🚨 **{data.get('threat')}**\n\n{data.get('post_text')}"
    try:
        await bot.send_message(chat_id=active_channel, text=final_post, parse_mode="Markdown")
        await callback.message.edit_text(
            f"✅ **Повідомлення успішно опубліковано в каналі `{active_channel}`!**", 
            parse_mode="Markdown"
        )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ **Помилка відправки в `{active_channel}`:**\n{e}\n\nПеревірте, чи додано бота в адміни цього каналу!", 
            parse_mode="Markdown"
        )
    await state.clear()

@dp.callback_query(F.data == "cancel_post")
async def cancel_post(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Публікацію скасовано. Для нового допису введіть /start")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
