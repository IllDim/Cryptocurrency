"""
Графический интерфейс приложения CryptoPulse.
Используется CustomTkinter для тёмной темы и карточного дизайна.
"""
import customtkinter as ctk
from typing import List, Dict, Any, Callable
import threading
import time

class CoinCard(ctk.CTkFrame):
    """Карточка для отображения одной криптовалюты."""

    def __init__(self, master, coin_data: Dict[str, Any], **kwargs):
        super().__init__(master, corner_radius=12, **kwargs)
        self.coin_data = coin_data
        self._build_ui()

    def _build_ui(self):
        # Верхняя строка: ранг + название + тикер
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(10, 4))

        rank = ctk.CTkLabel(
            top, text=f"#{self.coin_data.get('rank', '?')}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#888888"
        )
        rank.pack(side="left")

        name = ctk.CTkLabel(
            top,
            text=f"{self.coin_data.get('name', 'Unknown')}",
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w"
        )
        name.pack(side="left", padx=(8, 4))

        symbol = ctk.CTkLabel(
            top,
            text=f"({self.coin_data.get('symbol', '?')})",
            font=ctk.CTkFont(size=12),
            text_color="#aaaaaa"
        )
        symbol.pack(side="left")

        # Цена
        price = float(self.coin_data.get("price_usd", 0))
        price_label = ctk.CTkLabel(
            self,
            text=f"${price:,.6f}" if price < 1 else f"${price:,.2f}",
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="w"
        )
        price_label.pack(fill="x", padx=12, pady=(4, 2))

        # Изменение за 24ч + объём + капитализация
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=12, pady=(0, 10))

        change = float(self.coin_data.get("percent_change_24h", 0))
        color = "#2ecc71" if change >= 0 else "#e74c3c"
        arrow = "▲" if change >= 0 else "▼"
        change_label = ctk.CTkLabel(
            bottom,
            text=f"{arrow} {abs(change):.2f}%",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=color
        )
        change_label.pack(side="left")

        volume = self._format_number(self.coin_data.get("volume24", 0))
        mcap = self._format_number(self.coin_data.get("market_cap_usd", 0))
        info_label = ctk.CTkLabel(
            bottom,
            text=f"  Объём: {volume}  |  Кап: {mcap}",
            font=ctk.CTkFont(size=11),
            text_color="#999999"
        )
        info_label.pack(side="left", padx=(10, 0))

    @staticmethod
    def _format_number(value) -> str:
        try:
            num = float(value)
        except (TypeError, ValueError):
            return "N/A"
        if num >= 1_000_000_000:
            return f"{num/1_000_000_000:.2f}B"
        if num >= 1_000_000:
            return f"{num/1_000_000:.2f}M"
        if num >= 1_000:
            return f"{num/1_000:.2f}K"
        return f"{num:.2f}"


class CryptoPulseApp(ctk.CTk):
    """Главное окно приложения."""

    def __init__(self, api_client, refresh_interval: int = 60):
        super().__init__()
        self.api_client = api_client
        self.refresh_interval = refresh_interval
        self.cards: List[CoinCard] = []
        self._is_loading = False
        self._search_query = ""

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title("CryptoPulse — Монитор криптовалют")
        self.geometry("920x700+600+300")
        self.minsize(720, 500)

        self._build_header()
        self._build_content()
        self._build_status_bar()

        # Запуск первого обновления и автообновления
        self.after(200, self.refresh_data)
        self.after(1000, self._auto_refresh_tick)

    # ---------- Построение интерфейса ----------
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent", height=60)
        header.pack(fill="x", padx=20, pady=(15, 5))
        header.pack_propagate(False)

        title = ctk.CTkLabel(
            header,
            text="CryptoPulse",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#4da6ff"
        )
        title.pack(side="left")

        subtitle = ctk.CTkLabel(
            header,
            text="  живой криптотрекер",
            font=ctk.CTkFont(size=13),
            text_color="#777777"
        )
        subtitle.pack(side="left", padx=(4, 0))

        # Поиск
        self.search_entry = ctk.CTkEntry(
            header,
            placeholder_text="Поиск по тикеру...",
            width=180,
            height=32,
            corner_radius=8
        )
        self.search_entry.pack(side="right", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self._on_search)

        # Кнопка обновления
        self.refresh_btn = ctk.CTkButton(
            header,
            text="⟳  Обновить",
            width=120,
            height=32,
            corner_radius=8,
            fg_color="#1f6aa5",
            hover_color="#2a8cda",
            command=self.refresh_data
        )
        self.refresh_btn.pack(side="right")

    def _build_content(self):
        """Область с карточками монет."""
        self.content = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0
        )
        self.content.pack(fill="both", expand=True, padx=20, pady=(5, 10))

    def _build_status_bar(self):
        bar = ctk.CTkFrame(self, fg_color="transparent", height=30)
        bar.pack(fill="x", padx=20, pady=(0, 10))
        bar.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            bar,
            text="Готов к работе",
            font=ctk.CTkFont(size=11),
            text_color="#888888"
        )
        self.status_label.pack(side="left")

        self.countdown = ctk.CTkLabel(
            bar,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#4da6ff"
        )
        self.countdown.pack(side="right")

    # ---------- Работа с данными ----------
    def refresh_data(self):
        """Запускает обновление в отдельном потоке."""
        if self._is_loading:
            return
        self._is_loading = True
        self.refresh_btn.configure(state="disabled", text="Загрузка...")
        self.status_label.configure(text="Получение данных с CoinLore...")

        thread = threading.Thread(target=self._fetch_and_update, daemon=True)
        thread.start()

    def _fetch_and_update(self):
        """Сетевой запрос и обновление UI (вызывается в потоке)."""
        from api_client import POPULAR_COIN_IDS
        ids = list(POPULAR_COIN_IDS.keys())
        data = self.api_client.fetch_tickers(ids)

        # Возвращаемся в главный поток для обновления интерфейса
        self.after(0, lambda: self._update_ui(data))

    def _update_ui(self, data):
        """Обновляет карточки на основе полученных данных."""
        self._is_loading = False
        self.refresh_btn.configure(state="normal", text="⟳  Обновить")

        if not data:
            self.status_label.configure(text="⚠ Не удалось загрузить данные. Проверьте соединение.")
            return

        # Сортируем по рыночной капитализации (убывание)
        data.sort(key=lambda x: float(x.get("market_cap_usd", 0) or 0), reverse=True)

        # Очищаем старые карточки
        for card in self.cards:
            card.destroy()
        self.cards.clear()

        # Применяем фильтр поиска
        filtered = self._apply_search_filter(data)

        # Создаём новые карточки
        for coin in filtered:
            card = CoinCard(self.content, coin, fg_color="#1e1e24")
            card.pack(fill="x", pady=6)
            self.cards.append(card)

        now = time.strftime("%H:%M:%S")
        self.status_label.configure(
            text=f"✓ Обновлено в {now}  |  Показано {len(filtered)} монет"
        )

    def _apply_search_filter(self, data):
        """Фильтрует список по строке поиска."""
        if not self._search_query:
            return data
        q = self._search_query.upper()
        return [
            c for c in data
            if q in c.get("symbol", "").upper() or q in c.get("name", "").upper()
        ]

    def _on_search(self, event=None):
        """Обработчик ввода в поле поиска."""
        self._search_query = self.search_entry.get().strip()
        # Перерисовываем только если данные уже загружены
        if not self._is_loading and self.cards:
            # Запускаем повторную отрисовку с текущими данными
            # (данные хранятся в карточках, поэтому просто перезагружаем)
            self.refresh_data()

    # ---------- Автообновление ----------
    def _auto_refresh_tick(self):
        """Таймер автообновления."""
        if not self._is_loading:
            remaining = self.refresh_interval
            self._update_countdown(remaining)
            self.after(self.refresh_interval * 1000, self._auto_refresh_trigger)
        else:
            self.after(1000, self._auto_refresh_tick)

    def _auto_refresh_trigger(self):
        self.refresh_data()
        self.after(1000, self._auto_refresh_tick)

    def _update_countdown(self, seconds_left: int):
        """Обновляет счётчик до следующего автообновления."""
        def tick(s):
            if s > 0 and not self._is_loading:
                self.countdown.configure(text=f"Автообновление через {s} с")
                self.after(1000, lambda: tick(s - 1))
            else:
                self.countdown.configure(text="")
        tick(seconds_left)