# 🔌 API Reference - MeatBot

**Версия API:** 1.0.0
**Базовый URL:** `http://localhost:8000`
**Формат:** JSON

---

## 📋 Обзор

MeatBot предоставляет RESTful API для управления ботом, мониторинга состояния и интеграции с внешними системами.

---

## 🔐 Аутентификация

API использует простую аутентификацию через заголовки:

```http
Authorization: Bearer <your_token>
Content-Type: application/json
```

---

## 📊 Health Checks

### GET /health/live
Проверка жизнеспособности приложения.

**Ответ:**
```json
{
  "status": "live"
}
```

### GET /health/ready
Проверка готовности приложения к работе.

**Ответ:**
```json
{
  "status": "healthy",
  "checks": {
    "db": true,
    "redis": true
  }
}
```

**Коды ответов:**
- `200` - Приложение готово
- `503` - Приложение не готово

---

## 📚 Каталог товаров

### GET /api/catalog/categories
Получить список всех категорий.

**Параметры:**
- `active` (boolean, optional) - только активные категории

**Ответ:**
```json
[
  {
    "id": 1,
    "name": "Мясо",
    "description": "Свежее мясо",
    "image_url": "/static/images/categories/meat.jpg",
    "sort_order": 1,
    "is_active": true,
    "created_at": "2025-10-20T10:00:00Z",
    "updated_at": "2025-10-20T10:00:00Z"
  }
]
```

### GET /api/catalog/categories/{id}/products
Получить товары категории.

**Параметры:**
- `id` (integer) - ID категории
- `active` (boolean, optional) - только активные товары

**Ответ:**
```json
[
  {
    "id": 1,
    "name": "Говядина",
    "description": "Свежая говядина",
    "short_description": "Говядина премиум",
    "price": 500.00,
    "unit": "кг",
    "image_url": "/static/images/products/beef.jpg",
    "images": "[\"image1.jpg\", \"image2.jpg\"]",
    "category_id": 1,
    "sort_order": 1,
    "is_active": true,
    "is_available": true,
    "version": 1,
    "created_at": "2025-10-20T10:00:00Z",
    "updated_at": "2025-10-20T10:00:00Z"
  }
]
```

### GET /api/catalog/products/{id}
Получить товар по ID.

**Ответ:**
```json
{
  "id": 1,
  "name": "Говядина",
  "description": "Свежая говядина",
  "short_description": "Говядина премиум",
  "price": 500.00,
  "unit": "кг",
  "image_url": "/static/images/products/beef.jpg",
  "images": "[\"image1.jpg\", \"image2.jpg\"]",
  "category_id": 1,
  "sort_order": 1,
  "is_active": true,
  "is_available": true,
  "version": 1,
  "created_at": "2025-10-20T10:00:00Z",
  "updated_at": "2025-10-20T10:00:00Z"
}
```

### GET /api/catalog/search
Поиск товаров.

**Параметры:**
- `q` (string) - поисковый запрос
- `limit` (integer, optional) - лимит результатов (по умолчанию 50)

**Ответ:**
```json
[
  {
    "id": 1,
    "name": "Говядина",
    "price": 500.00,
    "unit": "кг",
    "image_url": "/static/images/products/beef.jpg",
    "category_id": 1
  }
]
```

---

## 🛒 Корзина

### GET /api/cart/{user_id}
Получить корзину пользователя.

**Ответ:**
```json
{
  "user_id": 123456789,
  "items": [
    {
      "id": 1,
      "product_id": 1,
      "product_name": "Говядина",
      "quantity": 2,
      "price_at_add": 500.00,
      "total_price": 1000.00,
      "notes": "Без костей"
    }
  ],
  "total_amount": 1000.00,
  "items_count": 2
}
```

### POST /api/cart/{user_id}/add
Добавить товар в корзину.

**Тело запроса:**
```json
{
  "product_id": 1,
  "quantity": 2,
  "notes": "Без костей"
}
```

**Ответ:**
```json
{
  "success": true,
  "message": "Товар добавлен в корзину",
  "cart_item": {
    "id": 1,
    "product_id": 1,
    "quantity": 2,
    "price_at_add": 500.00,
    "total_price": 1000.00
  }
}
```

### PUT /api/cart/{user_id}/items/{item_id}
Обновить товар в корзине.

**Тело запроса:**
```json
{
  "quantity": 3,
  "notes": "Обновленные заметки"
}
```

### DELETE /api/cart/{user_id}/items/{item_id}
Удалить товар из корзины.

**Ответ:**
```json
{
  "success": true,
  "message": "Товар удален из корзины"
}
```

### DELETE /api/cart/{user_id}
Очистить корзину.

**Ответ:**
```json
{
  "success": true,
  "message": "Корзина очищена"
}
```

---

## 📦 Заказы

### GET /api/orders
Получить список заказов (только для администраторов).

**Параметры:**
- `user_id` (integer, optional) - фильтр по пользователю
- `status` (string, optional) - фильтр по статусу
- `limit` (integer, optional) - лимит результатов
- `offset` (integer, optional) - смещение

**Ответ:**
```json
[
  {
    "id": 1,
    "order_number": "ORD-2025-001",
    "user_id": 123456789,
    "status": "pending",
    "payment_status": "pending",
    "payment_method": "card",
    "subtotal": 1000.00,
    "delivery_cost": 200.00,
    "total_amount": 1200.00,
    "delivery_address": "ул. Примерная, 1",
    "delivery_phone": "+7 900 123 45 67",
    "delivery_notes": "Домофон 123",
    "created_at": "2025-10-20T10:00:00Z",
    "updated_at": "2025-10-20T10:00:00Z",
    "items": [
      {
        "id": 1,
        "product_id": 1,
        "product_name": "Говядина",
        "product_unit": "кг",
        "product_price": 500.00,
        "quantity": 2,
        "total_price": 1000.00
      }
    ]
  }
]
```

### GET /api/orders/{order_id}
Получить заказ по ID.

**Ответ:**
```json
{
  "id": 1,
  "order_number": "ORD-2025-001",
  "user_id": 123456789,
  "status": "pending",
  "payment_status": "pending",
  "payment_method": "card",
  "subtotal": 1000.00,
  "delivery_cost": 200.00,
  "total_amount": 1200.00,
  "delivery_address": "ул. Примерная, 1",
  "delivery_phone": "+7 900 123 45 67",
  "delivery_notes": "Домофон 123",
  "created_at": "2025-10-20T10:00:00Z",
  "updated_at": "2025-10-20T10:00:00Z",
  "items": [
    {
      "id": 1,
      "product_id": 1,
      "product_name": "Говядина",
      "product_unit": "кг",
      "product_price": 500.00,
      "quantity": 2,
      "total_price": 1000.00
    }
  ]
}
```

### POST /api/orders
Создать новый заказ.

**Тело запроса:**
```json
{
  "user_id": 123456789,
  "payment_method": "card",
  "delivery_address": "ул. Примерная, 1",
  "delivery_phone": "+7 900 123 45 67",
  "delivery_notes": "Домофон 123",
  "delivery_cost": 200.00
}
```

**Ответ:**
```json
{
  "success": true,
  "order": {
    "id": 1,
    "order_number": "ORD-2025-001",
    "status": "pending",
    "total_amount": 1200.00
  }
}
```

### PUT /api/orders/{order_id}/status
Обновить статус заказа (только для администраторов).

**Тело запроса:**
```json
{
  "status": "confirmed"
}
```

**Ответ:**
```json
{
  "success": true,
  "message": "Статус заказа обновлен",
  "order": {
    "id": 1,
    "status": "confirmed"
  }
}
```

---

## 👥 Пользователи

### GET /api/users/{user_id}
Получить информацию о пользователе.

**Ответ:**
```json
{
  "id": 123456789,
  "username": "user123",
  "first_name": "Иван",
  "last_name": "Петров",
  "phone": "+7 900 123 45 67",
  "language_code": "ru",
  "is_active": true,
  "is_blocked": false,
  "created_at": "2025-10-20T10:00:00Z",
  "updated_at": "2025-10-20T10:00:00Z"
}
```

### GET /api/users
Получить список пользователей (только для администраторов).

**Параметры:**
- `limit` (integer, optional) - лимит результатов
- `offset` (integer, optional) - смещение
- `active` (boolean, optional) - фильтр по активности

---

## 👨‍💼 Администраторы

### GET /api/admin/stats
Получить статистику (только для администраторов).

**Ответ:**
```json
{
  "users": {
    "total": 150,
    "active": 120,
    "blocked": 5,
    "new_today": 3
  },
  "orders": {
    "total": 45,
    "pending": 5,
    "confirmed": 15,
    "completed": 20,
    "cancelled": 5
  },
  "products": {
    "total": 25,
    "active": 20,
    "inactive": 5
  },
  "revenue": {
    "today": 15000.00,
    "week": 85000.00,
    "month": 320000.00
  }
}
```

---

## 🖼️ Изображения

### POST /api/images/upload
Загрузить изображение.

**Тело запроса:** multipart/form-data
- `file` - файл изображения
- `type` - тип изображения (product, category)
- `product_id` (optional) - ID товара
- `category_id` (optional) - ID категории

**Ответ:**
```json
{
  "success": true,
  "image": {
    "id": 1,
    "filename": "product_123.webp",
    "url": "/static/images/products/product_123.webp",
    "size": 1024,
    "width": 400,
    "height": 400,
    "format": "WEBP"
  }
}
```

### GET /api/images/{image_id}
Получить информацию об изображении.

**Ответ:**
```json
{
  "id": 1,
  "filename": "product_123.webp",
  "url": "/static/images/products/product_123.webp",
  "size": 1024,
  "width": 400,
  "height": 400,
  "format": "WEBP",
  "created_at": "2025-10-20T10:00:00Z"
}
```

---

## 📊 Кэш

### GET /api/cache/stats
Получить статистику кэша (только для администраторов).

**Ответ:**
```json
{
  "redis": {
    "connected": true,
    "memory_used": "2.5MB",
    "keys_count": 150,
    "hit_rate": 0.85
  },
  "catalog": {
    "categories_cached": true,
    "products_cached": 25,
    "cache_size": "1.2MB"
  }
}
```

### DELETE /api/cache/catalog
Очистить кэш каталога (только для администраторов).

**Ответ:**
```json
{
  "success": true,
  "message": "Кэш каталога очищен"
}
```

---

## ❌ Обработка ошибок

### Коды ответов
- `200` - Успешный запрос
- `201` - Ресурс создан
- `400` - Неверный запрос
- `401` - Не авторизован
- `403` - Доступ запрещен
- `404` - Ресурс не найден
- `422` - Ошибка валидации
- `500` - Внутренняя ошибка сервера

### Формат ошибки
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Ошибка валидации данных",
    "details": {
      "field": "price",
      "message": "Цена должна быть больше 0"
    }
  }
}
```

---

## 🔄 Rate Limiting

API имеет ограничения на количество запросов:
- **Обычные пользователи:** 100 запросов в минуту
- **Администраторы:** 1000 запросов в минуту

При превышении лимита возвращается код `429 Too Many Requests`.

---

## 📝 Примеры использования

### JavaScript (fetch)
```javascript
// Получить категории
const response = await fetch('/api/catalog/categories');
const categories = await response.json();

// Добавить товар в корзину
const addToCart = await fetch('/api/cart/123456789/add', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    product_id: 1,
    quantity: 2
  })
});
```

### Python (requests)
```python
import requests

# Получить товары категории
response = requests.get('/api/catalog/categories/1/products')
products = response.json()

# Создать заказ
order_data = {
    'user_id': 123456789,
    'payment_method': 'card',
    'delivery_address': 'ул. Примерная, 1',
    'delivery_phone': '+7 900 123 45 67'
}
response = requests.post('/api/orders', json=order_data)
```

### cURL
```bash
# Получить статистику
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/admin/stats

# Загрузить изображение
curl -X POST \
     -H "Authorization: Bearer <token>" \
     -F "file=@image.jpg" \
     -F "type=product" \
     http://localhost:8000/api/images/upload
```

---

## 🔧 Webhook

### POST /webhook/telegram
Webhook для получения обновлений от Telegram.

**Тело запроса:** JSON с обновлением от Telegram Bot API

**Ответ:**
```json
{
  "success": true
}
```

---

**Последнее обновление:** 20.10.2025
**Версия API:** 1.0.0
