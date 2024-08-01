from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.config_reader import config
from app.services.database import get_all_users, get_blocked_users, get_user_statistics
from app.keyboards.admin import get_user_management_keyboard, get_user_statistics_keyboard
from app.states.admin import AdminStates

router = Router()


@router.callback_query(F.data == "list_users")
async def list_users(callback: CallbackQuery):
    if callback.from_user.id != config.admin_user_id:
        await callback.edit_text("У вас нет доступа к этой функции.", show_alert=True)
        return

    users = await get_all_users()
    user_list = "\n".join([f"ID: {user[0]}, Имя: {user[1]}, Возраст: {user[2]}" for user in users])

    if len(user_list) > 4096:
        # Если список слишком длинный, разделим его на части
        parts = [user_list[i:i + 4096] for i in range(0, len(user_list), 4096)]
        for part in parts:
            await callback.message.answer(part)
    else:
        await callback.message.edit_text(f"Список пользователей:\n\n{user_list}",
                                         reply_markup=get_user_management_keyboard())


@router.callback_query(F.data == "blocked_users")
async def show_blocked_users(callback: CallbackQuery):
    if callback.from_user.id != config.admin_user_id:
        await callback.edit_text("У вас нет доступа к этой функции.", show_alert=True)
        return

    blocked_users = await get_blocked_users()
    if not blocked_users:
        await callback.message.edit_text("Нет заблокированных пользователей.",
                                         reply_markup=get_user_management_keyboard())
        return

    user_list = "\n".join([f"ID: {user[0]}, Имя: {user[1]}, Причина: {user[2]}" for user in blocked_users])
    await callback.message.edit_text(f"Заблокированные пользователи:\n\n{user_list}",
                                     reply_markup=get_user_management_keyboard())


@router.callback_query(F.data == "block_user")
async def start_block_user(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != config.admin_user_id:
        await callback.edit_text("У вас нет доступа к этой функции.", show_alert=True)
        return

    await callback.message.edit_text("Введите ID пользователя, которого хотите заблокировать:")
    await state.set_state(AdminStates.waiting_for_user_id)


@router.callback_query(F.data == "unblock_user")
async def start_unblock_user(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != config.admin_user_id:
        await callback.edit_text("У вас нет доступа к этой функции.", show_alert=True)
        return

    await callback.message.edit_text("Введите ID пользователя, которого хотите разблокировать:")
    await state.set_state(AdminStates.waiting_for_user_id_unblock)


def format_user_statistics(stats):
    return (
        f"📊 Статистика пользователей:\n\n"
        f"👥 Всего пользователей: {stats['total_users']}\n"
        f"🟢 Активных пользователей: {stats['active_users']}\n"
        f"🔴 Заблокированных пользователей: {stats['blocked_users']}\n"
        f"🎲 Количество созданных сессий: {stats['total_sessions']}\n"
        f"📈 Среднее количество сессий на пользователя: {stats['avg_sessions_per_user']:.2f}"
    )


@router.callback_query(F.data == "user_statistics")
async def show_user_statistics(callback: CallbackQuery):
    if callback.from_user.id != config.admin_user_id:
        await callback.edit_text("У вас нет доступа к этой функции.", show_alert=True)
        return

    stats = await get_user_statistics()
    stats_text = format_user_statistics(stats)

    await callback.message.edit_text(
        stats_text,
        reply_markup=get_user_statistics_keyboard()
    )


@router.callback_query(F.data == "refresh_statistics")
async def refresh_statistics(callback: CallbackQuery):
    await show_user_statistics(callback)
