import os
import shutil
import time
from datetime import datetime

class ReportGenerator:
    def __init__(self, results, start_time, admin_id="Unknown"):
        self.results = results
        self.valid = [r for r in results if r['valid']]
        self.duration = int(time.time() - start_time)
        self.admin_id = admin_id
        self.temp_dir = f"temp_{int(start_time)}"
        self.report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def create_block(self, title, key, unit="", icon=""):
        total = sum(r.get(key, 0) for r in self.valid)
        active = [r for r in self.valid if r.get(key, 0) > 0]
        v_count = len(self.valid) if self.valid else 1
        perc = int((len(active) / v_count) * 100)
        avg = int(total / len(active)) if active else 0
        
        res = f"{icon} <b>{title}:</b> {total} ({perc}%, AVG: {avg})\nТоп {title.split()[-1]}:\n"
        top_items = sorted(self.valid, key=lambda x: x.get(key, 0), reverse=True)[:3]
        top_text = ""
        for i, acc in enumerate(top_items, 1):
            val = acc.get(key, 0)
            if val > 0:
                display_val = f"{val}{unit}" if key not in ['premium', 'voice'] else "Есть ✅"
                top_text += f"{i}) {display_val} — {acc['name']}  ❞\n"
        
        return res + f"<blockquote>{top_text if top_text else 'Список пуст ❞'}</blockquote>\n"

    def generate_stats_message(self):
        v = len(self.valid)
        if v == 0: return "❌ <b>Валидные аккаунты не найдены.</b>"
        msg = f"📊 <b>Отчёт о проверке:</b>\n\n📦 Всего: {len(self.results)}\n✅ Валид: {v}\n🕒 {self.duration} сек\n\n"
        msg += self.create_block("Robux", "robux", " R$", "💰")
        msg += self.create_block("All-time donate", "donate_all", "", "🕰")
        return msg

    def _generate_html(self):
        """Создает HTML отчет на основе твоего примера"""
        rows_html = ""
        for acc in self.valid:
            rows_html += f"""
            <tr>
                <td>{acc['name']}</td>
                <td>{acc['robux']} R$</td>
                <td>{acc['pending']} R$</td>
                <td>{acc['donate_all']}</td>
                <td>{acc['rap']}</td>
                <td>{'✅' if acc['premium'] else '❌'}</td>
                <td><button onclick="copyToClipboard('{acc['cookie']}')">Copy</button></td>
            </tr>
            """

        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Kuni Checker Report</title>
            <style>
                body {{ background: #050f16; color: #e6f7ff; font-family: 'Inter', sans-serif; }}
                .container {{ padding: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; background: rgba(10, 35, 45, 0.65); }}
                th, td {{ padding: 12px; border: 1px solid #1a3a4a; text-align: left; }}
                th {{ background: #ff3b3b; color: white; }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }}
                .stat-card {{ background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px; border-left: 4px solid #ff3b3b; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 Отчет для ID: {self.admin_id}</h1>
                <div class="stats-grid">
                    <div class="stat-card"><h3>Всего</h3><p>{len(self.results)}</p></div>
                    <div class="stat-card"><h3>Валид</h3><p>{len(self.valid)}</p></div>
                    <div class="stat-card"><h3>Robux</h3><p>{sum(r['robux'] for r in self.valid)}</p></div>
                    <div class="stat-card"><h3>Donate</h3><p>{sum(r['donate_all'] for r in self.valid)}</p></div>
                </div>
                <table>
                    <thead>
                        <tr><th>Username</th><th>Robux</th><th>Pending</th><th>Donate</th><th>RAP</th><th>Prem</th><th>Cookie</th></tr>
                    </thead>
                    <tbody>{rows_html}</tbody>
                </table>
            </div>
            <script>
                function copyToClipboard(text) {{
                    navigator.clipboard.writeText(text);
                    alert('Cookie скопирован!');
                }}
            </script>
        </body>
        </html>
        """
        return html_template

    def create_files(self):
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # 1. Текстовый файл с валидами
        with open(f"{self.temp_dir}/valids.txt", "w", encoding="utf-8") as f:
            for acc in self.valid: f.write(f"{acc['cookie']}\n")
        
        # 2. Красивый HTML отчет как в примере
        html_path = f"{self.temp_dir}/report_{int(time.time())}.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(self._generate_html())
        
        zip_name = f"result_{int(time.time())}"
        shutil.make_archive(zip_name, 'zip', self.temp_dir)
        shutil.rmtree(self.temp_dir)
        return zip_name + ".zip"
