from aiogram.fsm.state import State, StatesGroup


class SessionCreation(StatesGroup):
    choosing_game = State()
    setting_date = State()
    setting_time = State()
    setting_max_players = State()