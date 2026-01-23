"""
FSM состояния для пользователей.
"""

from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    """Состояния пользователя."""

    browsing_faq = State()
    viewing_category = State()
    viewing_question = State()
    searching = State()
    awaiting_search_query = State()
