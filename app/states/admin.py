from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_user_id_unblock = State()
    waiting_for_block_reason = State()
