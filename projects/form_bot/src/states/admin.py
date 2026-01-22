"""
Состояния конечного автомата для админ-панели.

Определяет состояния для навигации по админке и ответа клиентам.
"""

from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    """
    Состояния FSM для админ-панели.

    Attributes:
        waiting_for_reply: Ожидание текста ответа клиенту.
        confirm_delete: Ожидание подтверждения удаления заявки.
    """

    waiting_for_reply = State()
    confirm_delete = State()
