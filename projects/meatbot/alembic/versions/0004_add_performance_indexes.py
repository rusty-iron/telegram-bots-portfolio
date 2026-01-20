"""Add performance indexes

Revision ID: 0004
Revises: 0003
Create Date: 2025-10-20 18:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add performance indexes for frequently queried fields"""

    # Users table indexes
    op.create_index("ix_users_username", "users", ["username"], unique=False)
    op.create_index("ix_users_is_active", "users", ["is_active"], unique=False)
    op.create_index(
        "ix_users_is_blocked", "users", ["is_blocked"], unique=False
    )

    # Admin users table indexes
    op.create_index(
        "ix_admin_users_telegram_id",
        "admin_users",
        ["telegram_id"],
        unique=True,
    )
    op.create_index(
        "ix_admin_users_is_active", "admin_users", ["is_active"], unique=False
    )
    op.create_index(
        "ix_admin_users_role", "admin_users", ["role"], unique=False
    )

    # Categories table indexes
    op.create_index(
        "ix_categories_is_active", "categories", ["is_active"], unique=False
    )
    op.create_index(
        "ix_categories_sort_order", "categories", ["sort_order"], unique=False
    )
    op.create_index("ix_categories_name", "categories", ["name"], unique=False)

    # Products table indexes
    op.create_index(
        "ix_products_category_id", "products", ["category_id"], unique=False
    )
    op.create_index(
        "ix_products_is_active", "products", ["is_active"], unique=False
    )
    op.create_index(
        "ix_products_is_available", "products", ["is_available"], unique=False
    )
    op.create_index(
        "ix_products_sort_order", "products", ["sort_order"], unique=False
    )
    op.create_index("ix_products_name", "products", ["name"], unique=False)
    op.create_index("ix_products_price", "products", ["price"], unique=False)

    # Composite indexes for common queries
    op.create_index(
        "ix_products_category_active",
        "products",
        ["category_id", "is_active"],
        unique=False,
    )
    op.create_index(
        "ix_products_category_available",
        "products",
        ["category_id", "is_available"],
        unique=False,
    )

    # Cart items table indexes
    op.create_index(
        "ix_cart_items_user_id", "cart_items", ["user_id"], unique=False
    )
    op.create_index(
        "ix_cart_items_product_id", "cart_items", ["product_id"], unique=False
    )
    op.create_index(
        "ix_cart_items_user_product",
        "cart_items",
        ["user_id", "product_id"],
        unique=True,
    )

    # Orders table indexes
    op.create_index("ix_orders_user_id", "orders", ["user_id"], unique=False)
    op.create_index("ix_orders_status", "orders", ["status"], unique=False)
    op.create_index(
        "ix_orders_payment_status", "orders", ["payment_status"], unique=False
    )
    op.create_index(
        "ix_orders_created_at", "orders", ["created_at"], unique=False
    )
    op.create_index(
        "ix_orders_order_number", "orders", ["order_number"], unique=True
    )

    # Composite indexes for order queries
    op.create_index(
        "ix_orders_user_status", "orders", ["user_id", "status"], unique=False
    )
    op.create_index(
        "ix_orders_user_created",
        "orders",
        ["user_id", "created_at"],
        unique=False,
    )

    # Order items table indexes
    op.create_index(
        "ix_order_items_order_id", "order_items", ["order_id"], unique=False
    )
    op.create_index(
        "ix_order_items_product_id",
        "order_items",
        ["product_id"],
        unique=False,
    )

    # Timestamp indexes for all tables (for time-based queries)
    op.create_index(
        "ix_users_created_at", "users", ["created_at"], unique=False
    )
    op.create_index(
        "ix_admin_users_created_at",
        "admin_users",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_categories_created_at", "categories", ["created_at"], unique=False
    )
    op.create_index(
        "ix_products_created_at", "products", ["created_at"], unique=False
    )
    op.create_index(
        "ix_cart_items_created_at", "cart_items", ["created_at"], unique=False
    )
    op.create_index(
        "ix_order_items_created_at",
        "order_items",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Remove performance indexes"""

    # Remove timestamp indexes
    op.drop_index("ix_order_items_created_at", table_name="order_items")
    op.drop_index("ix_cart_items_created_at", table_name="cart_items")
    op.drop_index("ix_products_created_at", table_name="products")
    op.drop_index("ix_categories_created_at", table_name="categories")
    op.drop_index("ix_admin_users_created_at", table_name="admin_users")
    op.drop_index("ix_users_created_at", table_name="users")

    # Remove order items indexes
    op.drop_index("ix_order_items_product_id", table_name="order_items")
    op.drop_index("ix_order_items_order_id", table_name="order_items")

    # Remove order composite indexes
    op.drop_index("ix_orders_user_created", table_name="orders")
    op.drop_index("ix_orders_user_status", table_name="orders")

    # Remove order indexes
    op.drop_index("ix_orders_order_number", table_name="orders")
    op.drop_index("ix_orders_created_at", table_name="orders")
    op.drop_index("ix_orders_payment_status", table_name="orders")
    op.drop_index("ix_orders_status", table_name="orders")
    op.drop_index("ix_orders_user_id", table_name="orders")

    # Remove cart items indexes
    op.drop_index("ix_cart_items_user_product", table_name="cart_items")
    op.drop_index("ix_cart_items_product_id", table_name="cart_items")
    op.drop_index("ix_cart_items_user_id", table_name="cart_items")

    # Remove product composite indexes
    op.drop_index("ix_products_category_available", table_name="products")
    op.drop_index("ix_products_category_active", table_name="products")

    # Remove product indexes
    op.drop_index("ix_products_price", table_name="products")
    op.drop_index("ix_products_name", table_name="products")
    op.drop_index("ix_products_sort_order", table_name="products")
    op.drop_index("ix_products_is_available", table_name="products")
    op.drop_index("ix_products_is_active", table_name="products")
    op.drop_index("ix_products_category_id", table_name="products")

    # Remove category indexes
    op.drop_index("ix_categories_name", table_name="categories")
    op.drop_index("ix_categories_sort_order", table_name="categories")
    op.drop_index("ix_categories_is_active", table_name="categories")

    # Remove admin users indexes
    op.drop_index("ix_admin_users_role", table_name="admin_users")
    op.drop_index("ix_admin_users_is_active", table_name="admin_users")
    op.drop_index("ix_admin_users_telegram_id", table_name="admin_users")

    # Remove users indexes
    op.drop_index("ix_users_is_blocked", table_name="users")
    op.drop_index("ix_users_is_active", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
