"""
Состояния конечного автомата для формы сбора заявок.

Определяет последовательные шаги опроса пользователя.
"""

from aiogram.fsm.state import State, StatesGroup


class FormStates(StatesGroup):
    """
    Состояния FSM для процесса заполнения формы.

    Attributes:
        name: Ввод имени пользователя.
        phone: Ввод номера телефона.
        email: Ввод электронной почты.
        message: Ввод сообщения/комментария.
        confirm: Подтверждение введённых данных.
    """

    name = State()
    phone = State()
    email = State()
    message = State()
    confirm = State()
