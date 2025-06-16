import asyncio
import threading
from api.maimai50.maimaidx_update_plate import update_rating_table, update_plate_table
from api.maimai50.maimaidx_music import initialize_maimai_data
from loguru import logger as log
"""
def start_background_tasks():
    async def init_and_update():
        try:
            await initialize_maimai_data()
            log.info("开始初始化定数表和完成表")
            await update_rating_table()
            log.info("定数表首次更新完成")
            await update_plate_table()
            log.info("完成表首次更新完成")
        except Exception as e:
            log.exception(f"初始化或首次更新定数表/完成表出错: {e}")

        while True:
            try:
                await update_rating_table()
                log.info("定数表更新完成")
                await update_plate_table()
                log.info("完成表更新完成")
            except Exception as e:
                log.exception(f"定时更新定数表/完成表出错: {e}")
            await asyncio.sleep(24 * 60 * 60)  # 24小时

    def run_async_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(init_and_update())

    t = threading.Thread(target=run_async_loop, daemon=True)
    t.start()
"""

#start_background_tasks()