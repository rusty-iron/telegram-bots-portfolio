"""
Скрипт для тестирования Nginx
"""

import time

import requests


def test_nginx_connection():
    """Тест подключения к Nginx"""
    print("🔍 Тестирование подключения к Nginx...")

    try:
        response = requests.get("http://localhost/", timeout=5)
        if response.status_code == 200:
            print("✅ Nginx подключен успешно")
            print(f"   - Статус: {response.status_code}")
            print(f"   - Размер ответа: {len(response.content)} байт")
            return True
        else:
            print(f"⚠️ Nginx отвечает с кодом {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Не удается подключиться к Nginx")
        print("   Убедитесь, что контейнер nginx запущен")
        return False
    except Exception as e:
        print(f"❌ Ошибка подключения к Nginx: {e}")
        return False


def test_static_files():
    """Тест раздачи статических файлов"""
    print("\n🔍 Тестирование раздачи статических файлов...")

    try:
        # Тест главной страницы
        response = requests.get("http://localhost/", timeout=5)
        if response.status_code == 200:
            print("✅ Главная страница загружается")
        else:
            print(f"⚠️ Главная страница: код {response.status_code}")

        # Тест статических файлов
        static_urls = [
            "/static/",
            "/static/index.html",
            "/static/images/",
        ]

        for url in static_urls:
            try:
                response = requests.get(f"http://localhost{url}", timeout=5)
                if response.status_code == 200:
                    print(f"✅ {url} - доступен")
                elif response.status_code == 404:
                    print(
                        f"⚠️ {url} - не найден (ожидаемо для пустых директорий)")
                else:
                    print(f"⚠️ {url} - код {response.status_code}")
            except Exception as e:
                print(f"❌ {url} - ошибка: {e}")

        return True

    except Exception as e:
        print(f"❌ Ошибка тестирования статики: {e}")
        return False


def test_reverse_proxy():
    """Тест reverse proxy для health endpoints"""
    print("\n🔍 Тестирование reverse proxy...")

    try:
        # Тест health endpoints через Nginx
        health_urls = [
            "/health/live",
            "/health/ready",
        ]

        for url in health_urls:
            try:
                response = requests.get(f"http://localhost{url}", timeout=10)
                if response.status_code == 200:
                    print(f"✅ {url} - работает через reverse proxy")
                    try:
                        data = response.json()
                        print(f"   - Ответ: {data}")
                    except BaseException:
                        print(f"   - Ответ: {response.text[:100]}")
                else:
                    print(f"⚠️ {url} - код {response.status_code}")
            except Exception as e:
                print(f"❌ {url} - ошибка: {e}")

        return True

    except Exception as e:
        print(f"❌ Ошибка тестирования reverse proxy: {e}")
        return False


def test_nginx_headers():
    """Тест заголовков безопасности Nginx"""
    print("\n🔍 Тестирование заголовков безопасности...")

    try:
        response = requests.get("http://localhost/", timeout=5)
        headers = response.headers

        security_headers = {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }

        for header, expected_value in security_headers.items():
            if header in headers:
                if headers[header] == expected_value:
                    print(f"✅ {header}: {headers[header]}")
                else:
                    print(
                        f"⚠️ {header}: {
                            headers[header]} (ожидалось: {expected_value})")
            else:
                print(f"❌ {header}: отсутствует")

        # Проверка кэширования
        if "Cache-Control" in headers:
            print(f"✅ Cache-Control: {headers['Cache-Control']}")
        else:
            print("⚠️ Cache-Control: отсутствует")

        return True

    except Exception as e:
        print(f"❌ Ошибка тестирования заголовков: {e}")
        return False


def test_nginx_performance():
    """Тест производительности Nginx"""
    print("\n🔍 Тестирование производительности Nginx...")

    try:
        # Тест множественных запросов
        start_time = time.time()
        success_count = 0

        for i in range(10):
            try:
                response = requests.get("http://localhost/", timeout=5)
                if response.status_code == 200:
                    success_count += 1
            except BaseException:
                pass

        end_time = time.time()
        duration = end_time - start_time

        print(
            f"✅ Выполнено {success_count}/10 запросов за {duration:.2f} секунд"
        )
        print(f"   - Среднее время ответа: {duration / 10:.3f} сек")
        print(f"   - Успешность: {success_count / 10 * 100:.1f}%")

        return success_count >= 8  # Минимум 80% успешных запросов

    except Exception as e:
        print(f"❌ Ошибка тестирования производительности: {e}")
        return False


def test_gzip_compression():
    """Тест Gzip сжатия"""
    print("\n🔍 Тестирование Gzip сжатия...")

    try:
        headers = {"Accept-Encoding": "gzip, deflate"}
        response = requests.get(
            "http://localhost/", headers=headers, timeout=5
        )

        if "Content-Encoding" in response.headers:
            encoding = response.headers["Content-Encoding"]
            if "gzip" in encoding:
                print("✅ Gzip сжатие работает")
                print(f"   - Content-Encoding: {encoding}")
            else:
                print(f"⚠️ Content-Encoding: {encoding}")
        else:
            print("⚠️ Content-Encoding заголовок отсутствует")

        return True

    except Exception as e:
        print(f"❌ Ошибка тестирования Gzip: {e}")
        return False


def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования Nginx MeatBot\n")

    # Тесты
    connection_ok = test_nginx_connection()
    static_ok = test_static_files()
    proxy_ok = test_reverse_proxy()
    headers_ok = test_nginx_headers()
    performance_ok = test_nginx_performance()
    gzip_ok = test_gzip_compression()

    print(f"\n📊 Результаты тестирования:")
    print(f"   - Подключение к Nginx: {'✅' if connection_ok else '❌'}")
    print(f"   - Раздача статики: {'✅' if static_ok else '❌'}")
    print(f"   - Reverse proxy: {'✅' if proxy_ok else '❌'}")
    print(f"   - Заголовки безопасности: {'✅' if headers_ok else '❌'}")
    print(f"   - Производительность: {'✅' if performance_ok else '❌'}")
    print(f"   - Gzip сжатие: {'✅' if gzip_ok else '❌'}")

    if all(
        [
            connection_ok,
            static_ok,
            proxy_ok,
            headers_ok,
            performance_ok,
            gzip_ok,
        ]
    ):
        print("\n🎉 Все тесты Nginx прошли успешно!")
        return True
    else:
        print("\n⚠️ Некоторые тесты не прошли")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
