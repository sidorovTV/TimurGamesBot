from aiogram import Dispatcher

from .menu import router as menu_router
from .admin import router as admin_router
from .game_session import router as game_session_router


def register_callback(dp: Dispatcher):
    dp.include_router(menu_router)
    dp.include_router(admin_router)
    dp.include_router(game_session_router)