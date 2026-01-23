"""
Обработчик команд /start и /help.
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from keyboards.user import UserKeyboards
from utils.stats import StatsManager

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, stats: StatsManager) -> None:
    """Обработчик команды /start."""
    await state.clear()

    await stats.track_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    text = (
        f"Привет, {message.from_user.first_name}!\n\n"
        "Я бот с базой знаний. Могу помочь найти ответы на часто задаваемые вопросы.\n\n"
        "Выберите действие:"
    )

    await message.answer(text, reply_markup=UserKeyboards.main_menu())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Обработчик команды /help."""
    text = (
        "📚 Справка по боту\n\n"
        "🔹 /start - Начать работу с ботом\n"
        "🔹 /help - Показать эту справку\n"
        "🔹 /admin - Админ-панель (только для администратора)\n\n"
        "Используйте кнопки меню для навигации."
    )

    await message.answer(text)


@router.message(F.text == UserKeyboards.MAIN_MENU_BTN)
async def main_menu(message: Message, state: FSMContext) -> None:
    """Возврат в главное меню."""
    await state.clear()
    await message.answer(
        "Главное меню:",
        reply_markup=UserKeyboards.main_menu(),
    )
