"""Keyboards package for Telegram UI elements."""

from .admin import (
    get_admin_main_keyboard,
    get_categories_management_keyboard,
    get_category_actions_keyboard,
    get_category_list_keyboard,
    get_category_list_keyboard_with_pagination,
    get_photo_management_keyboard,
    get_product_actions_keyboard,
    get_product_list_keyboard,
    get_product_list_keyboard_with_pagination,
    get_products_for_photo_keyboard,
    get_products_management_keyboard,
)
from .cart import (
    get_cart_item_keyboard,
    get_quantity_change_keyboard,
    get_quantity_selection_keyboard,
)
from .catalog import get_catalog_products_keyboard

__all__ = [
    "get_admin_main_keyboard",
    "get_categories_management_keyboard",
    "get_category_actions_keyboard",
    "get_category_list_keyboard",
    "get_category_list_keyboard_with_pagination",
    "get_cart_item_keyboard",
    "get_catalog_products_keyboard",
    "get_photo_management_keyboard",
    "get_product_actions_keyboard",
    "get_product_list_keyboard",
    "get_product_list_keyboard_with_pagination",
    "get_products_for_photo_keyboard",
    "get_products_management_keyboard",
    "get_quantity_change_keyboard",
    "get_quantity_selection_keyboard",
]
