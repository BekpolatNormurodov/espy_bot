from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# 🔐 Token
TOKEN = '7136158913:AAFBYCzwtwLx0x7IQ0JszcwaGxLeBwB2590'
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# 🧠 Bosqichlar (holatlar)
class SearchForm(StatesGroup):
    region = State()
    district = State()
    job = State()
    salary = State()
    confirm = State()
    contact = State()

# 📍 Hududlar
regions = {
    "Toshkent": ["Chilonzor", "Yunusobod", "Yakkasaroy"],
    "Andijon": ["Asaka", "Andijon shahri", "Shahrixon"],
    "Navoiy": ["Zarafshon", "Karmana"]
}

# 🧾 Ishlar ro'yxati
jobs = [
    {
        "region": "Toshkent",
        "district": "Chilonzor",
        "job": "IT",
        "salary": 4000000,
        "company": "WebDev.uz",
        "description": "Frontend dasturchi kerak"
    },
    {
        "region": "Andijon",
        "district": "Asaka",
        "job": "Shifokor",
        "salary": 3000000,
        "company": "Asaka Shifoxonasi",
        "description": "Tajribali terapevt kerak"
    }
]

# ▶️ /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer("""
🏁 Assalomu alaykum! Sizga ish topishda yordam beradigan botga xush kelibsiz!

🤖 Bu bot orqali siz o'zingiz xohlagan viloyat va tumandan, o'zingizga mos soha va maoshdagi ishlarni topishingiz mumkin.

📝 Ish topish uchun ariza qoldiring:
👉 /ariza_qoldirish
""")

# 🔘 Ariza boshlash
@dp.message_handler(commands='ariza_qoldirish')
async def start_search(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    for r in regions:
        keyboard.add(InlineKeyboardButton(r, callback_data=f"region_{r}"))
    await message.answer("📍 Qaysi viloyatdan ish qidiryapsiz?", reply_markup=keyboard)
    await SearchForm.region.set()

# 📍 Viloyat tanlash
@dp.callback_query_handler(lambda c: c.data.startswith("region_"), state=SearchForm.region)
async def select_region(call: types.CallbackQuery, state: FSMContext):
    region = call.data.split("_")[1]
    await state.update_data(region=region)

    keyboard = InlineKeyboardMarkup()
    for d in regions[region]:
        keyboard.add(InlineKeyboardButton(d, callback_data=f"district_{d}"))
    await call.message.edit_text("🏙 Shahar/tumanni tanlang:", reply_markup=keyboard)
    await SearchForm.district.set()

# 🏙 Tuman tanlash
@dp.callback_query_handler(lambda c: c.data.startswith("district_"), state=SearchForm.district)
async def select_district(call: types.CallbackQuery, state: FSMContext):
    district = call.data.split("_")[1]
    await state.update_data(district=district)

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["👨‍💻 IT va dasturlash", "👩‍⚕ Shifokor / hamshira"]
    keyboard.add(*[KeyboardButton(text=b) for b in buttons])
    await call.message.answer("📋 O'zingizga mos ish sohasini tanlang:", reply_markup=keyboard)
    await SearchForm.job.set()

# 🛠 Kasb tanlash
@dp.message_handler(state=SearchForm.job)
async def select_job(message: types.Message, state: FSMContext):
    job_map = {
        "👨‍💻 IT va dasturlash": "IT",
        "👩‍⚕ Shifokor / hamshira": "Shifokor"
    }
    job_title = job_map.get(message.text)
    if not job_title:
        return await message.answer("❗ Iltimos, tugmalardan birini tanlang.")
    await state.update_data(job=job_title)
    await message.answer("💰 Sizni qoniqtiradigan eng kam oylikni yozing (Masalan: 3000000):")
    await SearchForm.salary.set()

# 💰 Maosh kiritish
@dp.message_handler(state=SearchForm.salary)
async def input_salary(message: types.Message, state: FSMContext):
    try:
        salary = int(message.text)
    except ValueError:
        return await message.answer("❌ Iltimos, raqam kiriting (Masalan: 3000000)")
    await state.update_data(salary=salary)
    data = await state.get_data()

    result = [
        j for j in jobs
        if j.get("region") == data["region"]
        and j.get("district") == data["district"]
        and j.get("job") == data["job"]
        and j.get("salary", 0) >= salary
    ]

    if not result:
        await message.answer("❌ Mos ish topilmadi.")
        return await state.finish()

    msg = "🔎 Topilgan ishlar:\n\n"
    for r in result:
        msg += f"🏢 {r['company']}\n📝 {r['description']}\n💰 {r['salary']} so'm\n\n"
    msg += "Zayavka qoldirasizmi?"

    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("✅ Ha", callback_data="confirm_yes"),
        InlineKeyboardButton("❌ Yo‘q", callback_data="confirm_no")
    )
    await message.answer(msg, reply_markup=keyboard)
    await SearchForm.confirm.set()

# ✅ Ha bosilganda
@dp.callback_query_handler(lambda c: c.data == "confirm_yes", state=SearchForm.confirm)
async def confirm_yes(call: types.CallbackQuery, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = KeyboardButton("📞 Kontaktni yuborish", request_contact=True)
    keyboard.add(button)
    await call.message.answer("📲 Telefon raqamingizni yuboring:", reply_markup=keyboard)
    await SearchForm.contact.set()

# ❌ Yo‘q bosilganda
@dp.callback_query_handler(lambda c: c.data == "confirm_no", state=SearchForm.confirm)
async def confirm_no(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("✅ Ariza bekor qilindi.")
    await state.finish()

# ☎️ Kontaktni qabul qilish
@dp.message_handler(content_types=types.ContentType.CONTACT, state=SearchForm.contact)
async def get_contact(message: types.Message, state: FSMContext):
    contact = message.contact.phone_number
    await state.update_data(contact=contact)
    await message.answer("✅ Zayavkangiz qabul qilindi! Tez orada siz bilan bog‘lanamiz.", reply_markup=ReplyKeyboardRemove())
    await state.finish()

# ▶️ Run
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
