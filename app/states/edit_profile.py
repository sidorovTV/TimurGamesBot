from aiogram.fsm.state import State, StatesGroup

class EditProfileStates(StatesGroup):
    choosing_field = State()
    editing_name = State()
    editing_age = State()