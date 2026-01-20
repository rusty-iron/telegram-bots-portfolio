"""
Create initial database schema

Revision ID: 0002
Revises: 0001_baseline
Create Date: 2025-01-27 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column(
            "id", sa.BigInteger(), nullable=False, comment="Telegram User ID"
        ),
        sa.Column(
            "username",
            sa.String(length=255),
            nullable=True,
            comment="Telegram username",
        ),
        sa.Column(
            "first_name",
            sa.String(length=255),
            nullable=False,
            comment="Имя пользователя",
        ),
        sa.Column(
            "last_name",
            sa.String(length=255),
            nullable=True,
            comment="Фамилия пользователя",
        ),
        sa.Column(
            "phone",
            sa.String(length=20),
            nullable=True,
            comment="Номер телефона",
        ),
        sa.Column(
            "language_code",
            sa.String(length=10),
            nullable=True,
            comment="Код языка пользователя",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            comment="Активен ли пользователь",
        ),
        sa.Column(
            "is_blocked",
            sa.Boolean(),
            nullable=False,
            comment="Заблокирован ли пользователь",
        ),
        sa.Column(
            "notes", sa.Text(), nullable=True, comment="Заметки о пользователе"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата создания записи",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата последнего обновления записи",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create categories table
    op.create_table(
        "categories",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
            comment="ID категории",
        ),
        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
            comment="Название категории",
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="Описание категории",
        ),
        sa.Column(
            "image_url",
            sa.String(length=500),
            nullable=True,
            comment="URL изображения категории",
        ),
        sa.Column(
            "sort_order",
            sa.Integer(),
            nullable=False,
            comment="Порядок сортировки категории",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            comment="Активна ли категория",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата создания записи",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата последнего обновления записи",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create products table
    op.create_table(
        "products",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
            comment="ID товара",
        ),
        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
            comment="Название товара",
        ),
        sa.Column(
            "description", sa.Text(), nullable=True, comment="Описание товара"
        ),
        sa.Column(
            "short_description",
            sa.String(length=500),
            nullable=True,
            comment="Краткое описание товара",
        ),
        sa.Column(
            "price",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
            comment="Цена товара",
        ),
        sa.Column(
            "unit",
            sa.String(length=50),
            nullable=False,
            comment="Единица измерения (кг, шт, упак)",
        ),
        sa.Column(
            "image_url",
            sa.String(length=500),
            nullable=True,
            comment="URL основного изображения товара",
        ),
        sa.Column(
            "images",
            sa.Text(),
            nullable=True,
            comment="JSON массив дополнительных изображений",
        ),
        sa.Column(
            "category_id",
            sa.Integer(),
            nullable=False,
            comment="ID категории товара",
        ),
        sa.Column(
            "sort_order",
            sa.Integer(),
            nullable=False,
            comment="Порядок сортировки товара в категории",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            comment="Активен ли товар",
        ),
        sa.Column(
            "is_available",
            sa.Boolean(),
            nullable=False,
            comment="Доступен ли товар для заказа",
        ),
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            comment="Версия записи для optimistic locking",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата создания записи",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата последнего обновления записи",
        ),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create cart_items table
    op.create_table(
        "cart_items",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
            comment="ID записи корзины",
        ),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            nullable=False,
            comment="ID пользователя",
        ),
        sa.Column(
            "product_id", sa.Integer(), nullable=False, comment="ID товара"
        ),
        sa.Column(
            "quantity",
            sa.Integer(),
            nullable=False,
            comment="Количество товара",
        ),
        sa.Column(
            "price_at_add",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
            comment="Цена товара на момент добавления в корзину",
        ),
        sa.Column(
            "notes",
            sa.String(length=500),
            nullable=True,
            comment="Заметки к товару в корзине",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата создания записи",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата последнего обновления записи",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "product_id", name="uq_cart_user_product"
        ),
    )

    # Create orders table
    op.create_table(
        "orders",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
            comment="ID заказа",
        ),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            nullable=False,
            comment="ID пользователя",
        ),
        sa.Column(
            "order_number",
            sa.String(length=50),
            nullable=False,
            comment="Номер заказа",
        ),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "CONFIRMED",
                "PROCESSING",
                "SHIPPED",
                "DELIVERED",
                "CANCELLED",
                "REFUNDED",
                name="orderstatus",
            ),
            nullable=False,
            comment="Статус заказа",
        ),
        sa.Column(
            "payment_status",
            sa.Enum(
                "PENDING", "PAID", "FAILED", "REFUNDED", name="paymentstatus"
            ),
            nullable=False,
            comment="Статус оплаты",
        ),
        sa.Column(
            "payment_method",
            sa.Enum("CARD", "CASH", "TRANSFER", name="paymentmethod"),
            nullable=False,
            comment="Способ оплаты",
        ),
        sa.Column(
            "subtotal",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
            comment="Сумма товаров без доставки",
        ),
        sa.Column(
            "delivery_cost",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
            comment="Стоимость доставки",
        ),
        sa.Column(
            "total_amount",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
            comment="Общая сумма заказа",
        ),
        sa.Column(
            "delivery_address",
            sa.Text(),
            nullable=False,
            comment="Адрес доставки",
        ),
        sa.Column(
            "delivery_phone",
            sa.String(length=20),
            nullable=False,
            comment="Телефон для доставки",
        ),
        sa.Column(
            "delivery_notes",
            sa.Text(),
            nullable=True,
            comment="Заметки к доставке",
        ),
        sa.Column(
            "confirmed_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Дата подтверждения заказа",
        ),
        sa.Column(
            "shipped_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Дата отправки заказа",
        ),
        sa.Column(
            "delivered_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Дата доставки заказа",
        ),
        sa.Column(
            "notes", sa.Text(), nullable=True, comment="Заметки к заказу"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата создания записи",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата последнего обновления записи",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_number"),
    )

    # Create order_items table
    op.create_table(
        "order_items",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
            comment="ID позиции заказа",
        ),
        sa.Column(
            "order_id", sa.Integer(), nullable=False, comment="ID заказа"
        ),
        sa.Column(
            "product_id", sa.Integer(), nullable=False, comment="ID товара"
        ),
        sa.Column(
            "product_name",
            sa.String(length=255),
            nullable=False,
            comment="Название товара на момент заказа",
        ),
        sa.Column(
            "product_unit",
            sa.String(length=50),
            nullable=False,
            comment="Единица измерения на момент заказа",
        ),
        sa.Column(
            "product_price",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
            comment="Цена товара на момент заказа",
        ),
        sa.Column(
            "quantity",
            sa.Integer(),
            nullable=False,
            comment="Количество товара",
        ),
        sa.Column(
            "total_price",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
            comment="Общая стоимость позиции",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата создания записи",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата последнего обновления записи",
        ),
        sa.ForeignKeyConstraint(
            ["order_id"], ["orders.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for better performance
    op.create_index("idx_users_username", "users", ["username"])
    op.create_index("idx_users_phone", "users", ["phone"])
    op.create_index("idx_categories_active", "categories", ["is_active"])
    op.create_index("idx_categories_sort", "categories", ["sort_order"])
    op.create_index("idx_products_category", "products", ["category_id"])
    op.create_index("idx_products_active", "products", ["is_active"])
    op.create_index("idx_products_available", "products", ["is_available"])
    op.create_index("idx_products_sort", "products", ["sort_order"])
    op.create_index("idx_cart_items_user", "cart_items", ["user_id"])
    op.create_index("idx_orders_user", "orders", ["user_id"])
    op.create_index("idx_orders_status", "orders", ["status"])
    op.create_index("idx_orders_payment_status", "orders", ["payment_status"])
    op.create_index("idx_orders_created", "orders", ["created_at"])
    op.create_index("idx_order_items_order", "order_items", ["order_id"])


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_order_items_order", table_name="order_items")
    op.drop_index("idx_orders_created", table_name="orders")
    op.drop_index("idx_orders_payment_status", table_name="orders")
    op.drop_index("idx_orders_status", table_name="orders")
    op.drop_index("idx_orders_user", table_name="orders")
    op.drop_index("idx_cart_items_user", table_name="cart_items")
    op.drop_index("idx_products_sort", table_name="products")
    op.drop_index("idx_products_available", table_name="products")
    op.drop_index("idx_products_active", table_name="products")
    op.drop_index("idx_products_category", table_name="products")
    op.drop_index("idx_categories_sort", table_name="categories")
    op.drop_index("idx_categories_active", table_name="categories")
    op.drop_index("idx_users_phone", table_name="users")
    op.drop_index("idx_users_username", table_name="users")

    # Drop tables in reverse order
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("cart_items")
    op.drop_table("products")
    op.drop_table("categories")
    op.drop_table("users")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS paymentmethod")
    op.execute("DROP TYPE IF EXISTS paymentstatus")
    op.execute("DROP TYPE IF EXISTS orderstatus")
