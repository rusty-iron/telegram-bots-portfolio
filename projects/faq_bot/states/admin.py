"""
FSM состояния для администратора.
"""

from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    """Состояния администратора."""

    main_menu = State()
    viewing_stats = State()
    awaiting_faq_file = State()
    confirming_upload = State()
