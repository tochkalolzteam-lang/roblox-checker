import aiohttp
import asyncio
import logging

logger = logging.getLogger(__name__)

class RobloxChecker:
    def __init__(self, concurrency: int = 10):
        # Ограничиваем количество одновременных проверок до 10 аккаунтов
        self.semaphore = asyncio.Semaphore(concurrency)

    async def _safe_get(self, session, url, headers):
        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
        except Exception as e:
            logger.error(f"Ошибка запроса {url}: {e}")
            return None

    async def check_account(self, cookie, session):
        async with self.semaphore:
            headers = {
                "Cookie": f".ROBLOSECURITY={cookie}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://www.roblox.com/"
            }
            
            data = {
                "cookie": cookie, "valid": False, "name": "Unknown", "id": 0,
                "robux": 0, "pending": 0, 
                "donate_year": 0, "donate_all": 0,
                "rap": 0, "followers": 0, "premium": False, "voice": False
            }

            try:
                # 1. Auth
                auth = await self._safe_get(session, "https://users.roblox.com/v1/users/authenticated", headers)
                if not auth: return data
                data.update({"id": auth["id"], "name": auth["name"], "valid": True})
                u_id = data['id']

                # 2. Parallel requests
                t1 = self._safe_get(session, f"https://premiumfeatures.roblox.com/v1/users/{u_id}/validate-membership", headers)
                t2 = self._safe_get(session, "https://voice.roblox.com/v1/settings", headers)
                t3 = self._safe_get(session, f"https://economy.roblox.com/v1/users/{u_id}/currency", headers)
                t4 = self._safe_get(session, f"https://friends.roblox.com/v1/users/{u_id}/followers/count", headers)
                
                res_prem, res_voice, res_curr, res_foll = await asyncio.gather(t1, t2, t3, t4)

                if res_prem is not None: data["premium"] = res_prem
                if res_voice: data["voice"] = res_voice.get("isVoiceEnabled", False)
                if res_curr: data["robux"] = res_curr.get("robux", 0)
                if res_foll: data["followers"] = res_foll.get("count", 0)

                # 3. REAL ECONOMY CALCULATION (Сумма, а не Максимум)
                # Берем данные за ВСЕ ВРЕМЯ
                all_res = await self._safe_get(session, f"https://economy.roblox.com/v2/users/{u_id}/transaction-totals?timeFrame=AllTime&transactionType=Summary", headers)
                
                if all_res:
                    data["pending"] = abs(all_res.get("pendingRobuxTotal", 0))
                    
                    # Считаем ВСЕ потоки денег:
                    # purchasesTotal = Потрачено в магазине
                    # salesOfGoodsTotal = Получено с продаж
                    # groupPayoutsTotal = Получено с групп (Важно!)
                    
                    purchases = abs(all_res.get("purchasesTotal", 0))
                    sales = abs(all_res.get("salesOfGoodsTotal", 0))
                    payouts = abs(all_res.get("groupPayoutsTotal", 0)) # Добавили выплаты с групп!
                    
                    # Теперь "All Time" это реальная сумма всего, что проходило через аккаунт
                    data["donate_all"] = purchases + sales + payouts

                # Данные за ГОД (для сравнения)
                year_res = await self._safe_get(session, f"https://economy.roblox.com/v2/users/{u_id}/transaction-totals?timeFrame=Year&transactionType=Summary", headers)
                if year_res:
                    y_purchases = abs(year_res.get("purchasesTotal", 0))
                    y_sales = abs(year_res.get("salesOfGoodsTotal", 0))
                    y_payouts = abs(year_res.get("groupPayoutsTotal", 0))
                    data["donate_year"] = y_purchases + y_sales + y_payouts

                # ФИНАЛЬНАЯ ПРОВЕРКА НА БАГ API
                # Если даже после суммирования "Все время" меньше "Года" -> это 100% баг API.
                # Мы не скрываем это, но используем данные года как "Минимально подтвержденные".
                if data["donate_all"] < data["donate_year"]:
                    data["donate_all"] = data["donate_year"]

                # 4. RAP
                rap_res = await self._safe_get(session, f"https://inventory.roblox.com/v1/users/{u_id}/assets/collectibles?limit=100", headers)
                if rap_res:
                    data["rap"] = sum(i.get("recentAveragePrice", 0) for i in rap_res.get("data", []))

            except Exception:
                pass
            
            return data

    async def process_cookies(self, cookies):
        # Отключаем SSL проверку и ставим таймаут 30 сек
        connector = aiohttp.TCPConnector(ssl=False)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = [self.check_account(c, session) for c in cookies]
            return await asyncio.gather(*tasks)