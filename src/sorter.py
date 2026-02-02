import os
import shutil
import time

class ReportGenerator:
    def __init__(self, results, start_time):
        self.results = results
        self.valid = [r for r in results if r['valid']]
        self.duration = int(time.time() - start_time) 
        self.temp_dir = f"temp_{int(start_time)}"

    def create_block(self, title, key, unit="", icon=""):
        # Суммируем всё для общего числа
        total = sum(r.get(key, 0) for r in self.valid)
        active = [r for r in self.valid if r.get(key, 0) > 0]
        v_count = len(self.valid) if self.valid else 1
        
        perc = int((len(active) / v_count) * 100)
        avg = int(total / len(active)) if active else 0
        
        # Единый дизайн заголовка
        res = f"{icon} <b>{title}:</b> {total} ({perc}%, AVG: {avg})\nТоп {title.split()[-1]}:\n"
        
        # Сортируем ТОП-3
        top_items = sorted(self.valid, key=lambda x: x.get(key, 0), reverse=True)[:3]
        top_text = ""
        for i, acc in enumerate(top_items, 1):
            val = acc.get(key, 0)
            if val > 0:
                # Для Premium/Voice убираем цифру "1", просто пишем имя
                display_val = f"{val}{unit}" if key not in ['premium', 'voice'] else "Есть ✅"
                top_text += f"{i}) {display_val} — {acc['name']}  ❞\n"
        
        if top_text:
            return res + f"<blockquote>{top_text.strip()}</blockquote>\n"
        return res + "<blockquote>Список пуст ❞</blockquote>\n"

    def generate_stats_message(self):
        v = len(self.valid)
        if v == 0: return "❌ <b>Валидные аккаунты не найдены.</b>"

        msg = "📊 <b>Отчёт о проверке:</b>\n\n"
        msg += f"📦 Всего куки: {len(self.results)}\n"
        msg += f"✅ Валидных: {v} | ❌ Невалидных: {len(self.results)-v}\n"
        msg += f"🕒 Время: {self.duration} сек\n\n"

        # ВСЕ блоки теперь в едином стиле
        msg += self.create_block("Robux", "robux", " R$", "💰")
        msg += self.create_block("Pending", "pending", " R$", "⏳")
        msg += self.create_block("1-year Donate", "donate_year", "", "💎")
        msg += self.create_block("All-time donate", "donate_all", "", "🕰")
        msg += self.create_block("Followers", "followers", "", "👥")
        msg += self.create_block("RAP", "rap", "", "🎩")
        msg += self.create_block("Premium", "premium", "", "⭐")
        msg += self.create_block("Voice Chat", "voice", "", "🎙")

        return msg

    def create_files(self):
        os.makedirs(self.temp_dir, exist_ok=True)
        with open(f"{self.temp_dir}/valids.txt", "w") as f:
            for acc in self.valid: f.write(f"{acc['cookie']}\n")
        
        # Исправлена кавычка (ошибка из image_4d9d7f.png)
        zip_name = f"result_{int(time.time())}"
        shutil.make_archive(zip_name, 'zip', self.temp_dir)
        shutil.rmtree(self.temp_dir)
        return zip_name + ".zip"