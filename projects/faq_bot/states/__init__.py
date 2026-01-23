"""FSM состояния бота."""

from states.user import UserStates
from states.admin import AdminStates

__all__ = ["UserStates", "AdminStates"]
