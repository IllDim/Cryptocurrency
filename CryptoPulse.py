"""
Точка входа приложения CryptoPulse.
Запускает GUI и управляет жизненным циклом.
"""
import sys
from api_client import CoinLoreClient
from gui import CryptoPulseApp


def main():
    client = CoinLoreClient(timeout=12)
    app = CryptoPulseApp(api_client=client, refresh_interval=60)
    try:
        app.mainloop()
    except KeyboardInterrupt:
        print("\nПриложение остановлено пользователем.")
        sys.exit(0)


if __name__ == "__main__":
    main()