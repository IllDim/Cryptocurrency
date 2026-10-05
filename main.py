"""
Приложение для отображения курсов криптовалют.
Использует CoinGecko API (демо-доступ, без API-ключа).
https://www.coingecko.com/en/api
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
from datetime import datetime

#Настройка конфигурации
API_URL = "https://api.coingecko.com/api/v3/simple/price"

COINS = {
    "bitcoin":  "Bitcoin (BTC)",
    "ethereum": "Ethereum (ETH)",
    "solana":   "Solana (SOL)",
    "cardano":  "Cardano (ADA)",
    "dogecoin": "Dogecoin (DOGE)",
}

REFRESH_INTERVAL_MS = 60_000  # 60 секунд
REQUEST_TIMEOUT = 10          # секунд


#API-клиент
def fetch_prices() -> dict[str, float] | None:
    """
    Запрашивает цены для списка монет в долларах США.
    Возвращает словарь {coin_id: price} или None при ошибке.
    """
    params = {
        "ids": ",".join(COINS.keys()),
        "vs_currencies": "usd",
    }
    try:
        response = requests.get(API_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        return {coin_id: data[coin_id]["usd"] for coin_id in COINS if coin_id in data}
    except requests.exceptions.RequestException as err:
        print(f"[Ошибка API] {err}")
        return None
    except (KeyError, ValueError) as err:
        print(f"[Ошибка парсинга] {err}")
        return None


#графический интерфейс приложения
class CryptoPriceApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("📈 Курс криптовалют")
        self.root.geometry("520x380+600+300")
        self.root.minsize(480, 340)
        self.root.configure(bg="#1e1e2e")

        self._build_ui()
        self._schedule_refresh(first_run=True)

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Treeview",
                        background="#2a2a3d",
                        foreground="white",
                        fieldbackground="#2a2a3d",
                        rowheight=32,
                        font=("Segoe UI", 11))
        style.configure("Treeview.Heading",
                        background="#3a3a5c",
                        foreground="white",
                        font=("Segoe UI", 11, "bold"))
        style.map("Treeview", background=[("selected", "#4a4a7a")])

        # Заголовок
        header = tk.Label(self.root, text="📈 Курс криптовалют",
                          font=("Segoe UI", 16, "bold"),
                          bg="#1e1e2e", fg="#89b4fa")
        header.pack(pady=(16, 8))

        # Таблица
        frame = tk.Frame(self.root, bg="#1e1e2e")
        frame.pack(fill="both", expand=True, padx=20, pady=8)

        columns = ("coin", "price")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=5)
        self.tree.heading("coin", text="Криптовалюта")
        self.tree.heading("price", text="Цена (USD)")
        self.tree.column("coin", anchor="w", width=220)
        self.tree.column("price", anchor="e", width=180)
        self.tree.pack(fill="both", expand=True)

        for coin_id, label in COINS.items():
            self.tree.insert("", "end", iid=coin_id, values=(label, "—"))

        # Нижняя панель
        bottom = tk.Frame(self.root, bg="#1e1e2e")
        bottom.pack(fill="x", padx=20, pady=(4, 16))

        self.refresh_btn = tk.Button(bottom, text="🔄 Обновить",
                                     font=("Segoe UI", 11, "bold"),
                                     bg="#89b4fa", fg="#1e1e2e",
                                     activebackground="#74a8e0",
                                     relief="flat", padx=16, pady=6,
                                     cursor="hand2",
                                     command=self._manual_refresh)
        self.refresh_btn.pack(side="left")

        self.status_var = tk.StringVar(value="Загрузка...")
        self.status_label = tk.Label(bottom, textvariable=self.status_var,
                                     font=("Segoe UI", 10),
                                     bg="#1e1e2e", fg="#a6adc8")
        self.status_label.pack(side="right")

    #Обновление данных
    def _manual_refresh(self):
        self._set_loading()
        threading.Thread(target=self._update_prices, daemon=True).start()

    def _schedule_refresh(self, first_run=False):
        if first_run:
            self._manual_refresh()
        self.root.after(REFRESH_INTERVAL_MS, self._auto_refresh)

    def _auto_refresh(self):
        self._set_loading()
        threading.Thread(target=self._update_prices, daemon=True).start()
        self._schedule_refresh()

    def _set_loading(self):
        self.status_var.set("Загрузка...")
        self.refresh_btn.config(state="disabled")

    def _update_prices(self):
        prices = fetch_prices()
        # Обновление GUI в главном потоке
        self.root.after(0, lambda: self._apply_prices(prices))

    def _apply_prices(self, prices: dict[str, float] | None):
        self.refresh_btn.config(state="normal")

        if prices is None:
            self.status_var.set("⚠ Ошибка загрузки. Повторите позже.")
            return

        for coin_id, price in prices.items():
            self.tree.set(coin_id, "price", f"$ {price:,.2f}")

        now = datetime.now().strftime("%H:%M:%S")
        self.status_var.set(f"Обновлено: {now}")

    #Запуск
    def run(self):
        self.root.mainloop()


# main
if __name__ == "__main__":
    root = tk.Tk()
    app = CryptoPriceApp(root)
    app.run()


