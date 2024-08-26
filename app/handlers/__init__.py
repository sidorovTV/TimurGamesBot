from aiogram import Dispatcher
from .start import router as start_router
from .registration import router as registration_router
from .game_session import router as game_session_router
from .help import router as help_router
from .admin import router as admin_router
from .edit_profile import router as edit_profile_router
from .common import router as common_router
def register_handlers(dp: Dispatcher):
    dp.include_router(start_router)
    dp.include_router(registration_router)
    dp.include_router(game_session_router)
    dp.include_router(help_router)
    dp.include_router(admin_router)
    dp.include_router(edit_profile_router)
    dp.include_router(common_router)
