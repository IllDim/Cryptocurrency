"""
Модуль для взаимодействия с CoinLore API.
Документация: https://www.coinlore.com/ru/cryptocurrency-data-api
"""
import requests
from typing import List, Dict, Any, Optional

BASE_URL = "https://api.coinlore.net/api"

# ID популярных монет в CoinLore (получены через /api/assets/)
POPULAR_COIN_IDS = {
    "90": "BTC",   # Bitcoin
    "80": "ETH",   # Ethereum
    "518": "USDT", # Tether
    "2710": "BNB", # Binance Coin
    "48543": "SOL",# Solana
    "58": "XRP",   # XRP
    "257": "ADA",  # Cardano
    "2": "DOGE",   # Dogecoin
    "45219": "DOT",# Polkadot
    "1": "LTC",    # Litecoin
}

class CoinLoreClient:
    """Клиент для получения тикеров с CoinLore."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "CryptoPulse/1.0"})

    def fetch_tickers(self, coin_ids: List[str]) -> Optional[List[Dict[str, Any]]]:
        """
        Запрашивает данные для указанных ID монет.
        Возвращает список словарей или None при ошибке.
        """
        ids_param = ",".join(coin_ids)
        url = f"{BASE_URL}/ticker/?id={ids_param}"
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            # API возвращает список словарей
            if isinstance(data, list):
                return data
            return None
        except requests.RequestException as err:
            print(f"[API] Ошибка запроса: {err}")
            return None

    def fetch_global(self) -> Optional[Dict[str, Any]]:
        """Возвращает глобальную статистику рынка."""
        url = f"{BASE_URL}/global/"
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data[0] if data else None
        except requests.RequestException:
            return None