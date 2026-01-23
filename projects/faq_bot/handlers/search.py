"""
Обработчики поиска по FAQ.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from keyboards.user import UserKeyboards
from states.user import UserStates
from utils.search import FAQSearch
from utils.stats import StatsManager

router = Router(name="search")


@router.message(F.text == UserKeyboards.SEARCH_BTN)
async def start_search(message: Message, state: FSMContext) -> None:
    """Начать поиск."""
    await state.set_state(UserStates.awaiting_search_query)

    await message.answer(
        "🔍 Введите поисковый запрос\n\n"
        "Минимум 2 символа:",
        reply_markup=UserKeyboards.cancel_search(),
    )


@router.message(F.text == "❌ Отмена")
async def cancel_search_btn(message: Message, state: FSMContext) -> None:
    """Отмена поиска кнопкой."""
    await state.clear()
    await message.answer(
        "Поиск отменен.",
        reply_markup=UserKeyboards.main_menu(),
    )


@router.callback_query(F.data == "cancel_search")
async def cancel_search(callback: CallbackQuery, state: FSMContext) -> None:
    """Отмена поиска."""
    await state.clear()
    await callback.message.edit_text("Поиск завершен.")
    await callback.message.answer(
        "Главное меню:",
        reply_markup=UserKeyboards.main_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "new_search")
async def new_search(callback: CallbackQuery, state: FSMContext) -> None:
    """Новый поиск."""
    await state.set_state(UserStates.awaiting_search_query)

    await callback.message.edit_text(
        "🔍 Введите новый поисковый запрос\n\n"
        "Минимум 2 символа:"
    )
    await callback.answer()


@router.message(UserStates.awaiting_search_query)
async def process_search(
    message: Message,
    state: FSMContext,
    faq_search: FAQSearch,
    stats: StatsManager,
) -> None:
    """Обработка поискового запроса."""
    query = message.text.strip()

    if len(query) < 2:
        await message.answer(
            "Запрос слишком короткий. Минимум 2 символа.",
        )
        return

    results = faq_search.search(query)

    await stats.track_search(
        user_id=message.from_user.id,
        query=query,
        results_count=len(results),
    )

    if not results:
        await message.answer(
            f"🔍 По запросу \"{query}\" ничего не найдено.\n\n"
            "Попробуйте другой запрос или обратитесь в поддержку.",
            reply_markup=UserKeyboards.back_to_search(),
        )
        return

    await state.set_state(UserStates.searching)
    await state.update_data(search_results=results, search_query=query)

    text = f"🔍 Результаты поиска по \"{query}\":\n\nНайдено: {len(results)}"

    await message.answer(
        text,
        reply_markup=UserKeyboards.search_results(results),
    )


@router.callback_query(F.data.startswith("sr:"), UserStates.searching)
async def show_search_result(
    callback: CallbackQuery,
    state: FSMContext,
    stats: StatsManager,
) -> None:
    """Показать результат поиска."""
    data = await state.get_data()
    results = data.get("search_results", [])

    try:
        result_idx = int(callback.data[3:])
        result = results[result_idx]
    except (ValueError, IndexError):
        await callback.answer("Результат не найден", show_alert=True)
        return

    await stats.track_faq_view(
        user_id=callback.from_user.id,
        category=result.category,
        question=result.question,
    )

    text = (
        f"📁 {result.category}\n\n"
        f"❓ {result.question}\n\n"
        f"📝 {result.answer}"
    )

    if len(text) > 4096:
        text = text[:4093] + "..."

    await callback.message.edit_text(
        text,
        reply_markup=UserKeyboards.back_to_search(),
    )
    await callback.answer()
