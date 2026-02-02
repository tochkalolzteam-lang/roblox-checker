import asyncio
import logging
from src.bot import bot, dp
from src.handlers import router
from keep_alive import start_server # <--- ДОБАВИЛ

async def main():
    logging.basicConfig(level=logging.INFO)
    dp.include_router(router)
    
    print(">>> БОТ ЗАПУЩЕН! ЖДУ КУКИ...")
    await bot.delete_webhook(drop_pending_updates=True)
    
    await start_server() # <--- ДОБАВИЛ (Важно!)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")