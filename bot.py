from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import logging

TOKEN = '7136158913:AAFBYCzwtwLx0x7IQ0JszcwaGxLeBwB2590'
ADMIN_ID = 123456789  # o'zingizning Telegram ID'ingizni yozing

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

regions = {
    "Toshkent": ["Yunusobod", "Chilonzor"],
    "Andijon": ["Asaka", "Shahrixon"],
}
categories = ["Dasturchi", "Haydovchi"]

# Lokal ish ro'yxati (test ma'lumotlar)
jobs_data = [
    {
        "region": "Toshkent",
        "district": "Yunusobod",
        "job": "Dasturchi",
        "salary": 5000000,
        "company": "ProActive MCHJ",
        "description": "Shopping dastur tuzish kerak"
    },
    {
        "region": "Toshkent",
        "district": "Chilonzor",
        "job": "Haydovchi",
        "salary": 3000000,
        "company": "FastGo",
        "description": "Yuk tashish uchun haydovchi kerak"
    }
]

class SearchForm(StatesGroup):
    region = State()
    district = State()
    category = State()
    salary = State()
    confirm = State()
    contact = State()
    location = State()

@dp.message_handler(commands='start')
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    for r in regions:
        keyboard.add(InlineKeyboardButton(r, callback_data=f"region_{r}"))
    await message.answer("📍 Qaysi viloyatda ish qidiryapsiz?", reply_markup=keyboard)
    await SearchForm.region.set()

@dp.callback_query_handler(lambda c: c.data.startswith("region_"), state=SearchForm.region)
async def select_region(call: types.CallbackQuery, state: FSMContext):
    region = call.data.split("_")[1]
    await state.update_data(region=region)
    keyboard = InlineKeyboardMarkup()
    for d in regions[region]:
        keyboard.add(InlineKeyboardButton(d, callback_data=f"district_{d}"))
    await call.message.edit_text("🏙 Tuman/shaharni tanlang:", reply_markup=keyboard)
    await SearchForm.district.set()

@dp.callback_query_handler(lambda c: c.data.startswith("district_"), state=SearchForm.district)
async def select_district(call: types.CallbackQuery, state: FSMContext):
    district = call.data.split("_")[1]
    await state.update_data(district=district)
    keyboard = InlineKeyboardMarkup()
    for c in categories:
        keyboard.add(InlineKeyboardButton(c, callback_data=f"job_{c}"))
    await call.message.edit_text("👷 Kasb turini tanlang:", reply_markup=keyboard)
    await SearchForm.category.set()

@dp.callback_query_handler(lambda c: c.data.startswith("job_"), state=SearchForm.category)
async def select_job(call: types.CallbackQuery, state: FSMContext):
    job = call.data.split("_")[1]
    await state.update_data(job=job)
    await call.message.answer("💰 Kamida qancha maosh kerak?")
    await SearchForm.salary.set()

@dp.message_handler(state=SearchForm.salary)
async def input_salary(message: types.Message, state: FSMContext):
    try:
        salary = int(message.text)
    except ValueError:
        return await message.reply("Iltimos, faqat son kiriting!")
    await state.update_data(salary=salary)
    data = await state.get_data()

    # Filter ishlar
    result = [
        j for j in jobs_data
        if j['region'] == data['region'] and j['district'] == data['district'] and j['job'] == data['job'] and j['salary'] >= salary
    ]

    if not result:
        await message.answer("❌ Mos ish topilmadi.")
        return await state.finish()

    msg = "🔎 Topilgan ishlar:\n\n"
    for r in result:
        msg += f"🏢 {r['company']}\n📝 {r['description']}\n💰 {r['salary']} so‘m\n\n"
    msg += "Zayavka qoldirasizmi?"

    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("✅ Ha", callback_data="confirm_yes"),
        InlineKeyboardButton("❌ Yo‘q", callback_data="confirm_no")
    )
    await message.answer(msg, reply_markup=keyboard)
    await SearchForm.confirm.set()

@dp.callback_query_handler(lambda c: c.data in ["confirm_yes", "confirm_no"], state=SearchForm.confirm)
async def confirm_application(call: types.CallbackQuery, state: FSMContext):
    if call.data == "confirm_no":
        await call.message.edit_text("❌ Zayavka bekor qilindi.")
        return await state.finish()

    # Agar Ha desa — contact so‘raymiz
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton("📞 Kontaktni yuborish", request_contact=True))
    await call.message.answer("📞 Telefon raqamingizni yuboring:", reply_markup=keyboard)
    await SearchForm.contact.set()

@dp.message_handler(content_types=types.ContentType.CONTACT, state=SearchForm.contact)
async def get_contact(message: types.Message, state: FSMContext):
    await state.update_data(contact=message.contact.phone_number)
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton("📍 Lokatsiyani yuborish", request_location=True))
    await message.answer("📍 Lokatsiyangizni yuboring:", reply_markup=keyboard)
    await SearchForm.location.set()

@dp.message_handler(content_types=types.ContentType.LOCATION, state=SearchForm.location)
async def get_location(message: types.Message, state: FSMContext):
    lat = message.location.latitude
    lon = message.location.longitude
    loc_link = f"https://maps.google.com/?q={lat},{lon}"
    await state.update_data(location=loc_link)
    data = await state.get_data()

    # Admin yoki botga xabar
    await message.answer("✅ Zayavkangiz qabul qilindi! Rahmat.", reply_markup=types.ReplyKeyboardRemove())
    await bot.send_message(ADMIN_ID, f"🆕 Yangi zayavka:\nTel: {data['contact']}\nLocation: {data['location']}")
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)