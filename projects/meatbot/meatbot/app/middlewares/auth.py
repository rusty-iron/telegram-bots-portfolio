"""
Middleware для аутентификации и авторизации
"""

import base64
from typing import Dict, Optional

import structlog
from aiohttp import web
from aiohttp.web import Request, Response

logger = structlog.get_logger()


class AuthMiddleware:
    """Middleware для аутентификации HTTP запросов"""

    def __init__(self, api_key: str, admin_key: Optional[str] = None):
        self.api_key = api_key
        self.admin_key = admin_key or api_key

    async def __call__(self, request: Request, handler) -> Response:
        """Проверка аутентификации для защищенных endpoints"""

        # Проверяем, требует ли endpoint аутентификации
        if not self._requires_auth(request.path):
            return await handler(request)

        # Получаем заголовки аутентификации
        auth_header = request.headers.get("Authorization")
        api_key_header = request.headers.get("X-API-Key")

        # Проверяем API ключ
        if api_key_header:
            if api_key_header == self.api_key:
                request["auth_level"] = "api"
                return await handler(request)
            elif api_key_header == self.admin_key:
                request["auth_level"] = "admin"
                return await handler(request)

        # Проверяем Basic Auth
        if auth_header and auth_header.startswith("Basic "):
            try:
                credentials = base64.b64decode(auth_header[6:]).decode("utf-8")
                username, password = credentials.split(":", 1)

                if username == "admin" and password == self.admin_key:
                    request["auth_level"] = "admin"
                    return await handler(request)
                elif username == "api" and password == self.api_key:
                    request["auth_level"] = "api"
                    return await handler(request)
            except Exception as e:
                logger.warning("auth_basic_decode_failed", error=str(e))

        # Если аутентификация не прошла
        logger.warning("auth_failed", path=request.path, ip=request.remote)
        return web.json_response(
            {"error": "Unauthorized", "message": "Invalid credentials"},
            status=401,
            headers={"WWW-Authenticate": 'Basic realm="MeatBot API"'},
        )

    def _requires_auth(self, path: str) -> bool:
        """Определяет, требует ли путь аутентификации"""
        protected_paths = [
            "/metrics",
            "/admin/",
            "/api/",
        ]

        return any(path.startswith(protected) for protected in protected_paths)


class RateLimitMiddleware:
    """Middleware для ограничения частоты запросов"""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = {}

    async def __call__(self, request: Request, handler) -> Response:
        """Проверка лимита запросов"""

        # Получаем IP адрес клиента
        client_ip = self._get_client_ip(request)

        # Проверяем лимит
        if not self._check_rate_limit(client_ip):
            logger.warning(
                "rate_limit_exceeded", ip=client_ip, path=request.path
            )
            return web.json_response(
                {
                    "error": "Rate limit exceeded",
                    "message": "Too many requests",
                },
                status=429,
                headers={"Retry-After": str(self.window_seconds)},
            )

        return await handler(request)

    def _get_client_ip(self, request: Request) -> str:
        """Получает IP адрес клиента"""
        # Проверяем заголовки прокси
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.remote

    def _check_rate_limit(self, client_ip: str) -> bool:
        """Проверяет, не превышен ли лимит запросов"""
        import time

        current_time = time.time()

        # Очищаем старые запросы
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time
                for req_time in self.requests[client_ip]
                if current_time - req_time < self.window_seconds
            ]
        else:
            self.requests[client_ip] = []

        # Проверяем лимит
        if len(self.requests[client_ip]) >= self.max_requests:
            return False

        # Добавляем текущий запрос
        self.requests[client_ip].append(current_time)
        return True


@web.middleware
async def security_headers_middleware(request: Request, handler) -> Response:
    """Middleware для добавления заголовков безопасности"""
    response = await handler(request)

    # Добавляем заголовки безопасности
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'"

    # Добавляем заголовок для API
    if request.path.startswith("/api/"):
        response.headers["X-API-Version"] = "1.0.0"

    return response


def setup_security_middleware(
    app: web.Application, api_key: str, admin_key: Optional[str] = None
) -> None:
    """Настройка middleware безопасности"""

    # Создаем экземпляры middleware классов
    auth_middleware_instance = AuthMiddleware(api_key, admin_key)
    rate_limit_middleware_instance = RateLimitMiddleware()

    # Создаем middleware factories для классов
    @web.middleware
    async def auth_middleware(request, handler):
        return await auth_middleware_instance(request, handler)

    @web.middleware
    async def rate_limit_middleware(request, handler):
        return await rate_limit_middleware_instance(request, handler)

    # Добавляем middleware
    app.middlewares.append(auth_middleware)
    app.middlewares.append(rate_limit_middleware)
    app.middlewares.append(security_headers_middleware)

    logger.info("security_middleware_configured")
