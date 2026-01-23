"""
Обработчики FAQ навигации.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from keyboards.user import UserKeyboards
from states.user import UserStates
from utils.faq_loader import FAQLoader
from utils.stats import StatsManager

router = Router(name="faq")


@router.message(F.text == UserKeyboards.FAQ_BTN)
async def show_categories(
    message: Message,
    state: FSMContext,
    faq_loader: FAQLoader,
) -> None:
    """Показать категории FAQ."""
    await state.set_state(UserStates.browsing_faq)

    categories = faq_loader.get_categories()

    if not categories:
        await message.answer(
            "FAQ пока пуст. Попробуйте позже.",
            reply_markup=UserKeyboards.main_menu(),
        )
        return

    await message.answer(
        "📚 Выберите категорию:",
        reply_markup=UserKeyboards.categories(categories),
    )


@router.callback_query(F.data.startswith("cat:"))
async def show_category_questions(
    callback: CallbackQuery,
    state: FSMContext,
    faq_loader: FAQLoader,
) -> None:
    """Показать вопросы категории."""
    category = callback.data[4:]

    full_category = None
    for cat in faq_loader.get_categories():
        if cat.startswith(category) or cat == category:
            full_category = cat
            break

    if not full_category:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    questions = faq_loader.get_questions(full_category)

    if not questions:
        await callback.answer("В этой категории пока нет вопросов", show_alert=True)
        return

    await state.set_state(UserStates.viewing_category)
    await state.update_data(
        current_category=full_category,
        questions=list(questions.keys()),
    )

    await callback.message.edit_text(
        f"{full_category}\n\nВыберите вопрос:",
        reply_markup=UserKeyboards.questions(full_category, list(questions.keys())),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("q:"))
async def show_answer(
    callback: CallbackQuery,
    state: FSMContext,
    faq_loader: FAQLoader,
    stats: StatsManager,
) -> None:
    """Показать ответ на вопрос."""
    data = await state.get_data()
    category = data.get("current_category")
    questions = data.get("questions", [])

    try:
        question_idx = int(callback.data[2:])
        question = questions[question_idx]
    except (ValueError, IndexError):
        await callback.answer("Вопрос не найден", show_alert=True)
        return

    answer = faq_loader.get_answer(category, question)

    if not answer:
        await callback.answer("Ответ не найден", show_alert=True)
        return

    await stats.track_faq_view(
        user_id=callback.from_user.id,
        category=category,
        question=question,
    )

    await state.set_state(UserStates.viewing_question)

    text = f"❓ {question}\n\n📝 {answer}"

    if len(text) > 4096:
        text = text[:4093] + "..."

    await callback.message.edit_text(
        text,
        reply_markup=UserKeyboards.answer_navigation(category),
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(
    callback: CallbackQuery,
    state: FSMContext,
    faq_loader: FAQLoader,
) -> None:
    """Вернуться к списку категорий."""
    await state.set_state(UserStates.browsing_faq)

    categories = faq_loader.get_categories()

    await callback.message.edit_text(
        "📚 Выберите категорию:",
        reply_markup=UserKeyboards.categories(categories),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("back_to_cat:"))
async def back_to_category(
    callback: CallbackQuery,
    state: FSMContext,
    faq_loader: FAQLoader,
) -> None:
    """Вернуться к вопросам категории."""
    category_prefix = callback.data[12:]

    full_category = None
    for cat in faq_loader.get_categories():
        if cat.startswith(category_prefix) or cat == category_prefix:
            full_category = cat
            break

    if not full_category:
        await back_to_categories(callback, state, faq_loader)
        return

    questions = faq_loader.get_questions(full_category)

    await state.set_state(UserStates.viewing_category)
    await state.update_data(
        current_category=full_category,
        questions=list(questions.keys()),
    )

    await callback.message.edit_text(
        f"{full_category}\n\nВыберите вопрос:",
        reply_markup=UserKeyboards.questions(full_category, list(questions.keys())),
    )
    await callback.answer()


@router.message(F.text == UserKeyboards.SUPPORT_BTN)
async def show_support(
    message: Message,
    stats: StatsManager,
    support_username: str,
) -> None:
    """Показать контакт поддержки."""
    await stats.track_support_request(
        user_id=message.from_user.id,
        username=message.from_user.username,
    )

    await message.answer(
        "💬 Связаться с поддержкой\n\n"
        "Если вы не нашли ответ на свой вопрос, "
        "свяжитесь с нашей службой поддержки:",
        reply_markup=UserKeyboards.support_contact(support_username),
    )
