from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.config_reader import config
from app.services.database import get_all_users, block_user, unblock_user, get_blocked_users, get_user_statistics
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.utils.message_cleaner import message_cleaner

router = Router()


class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_block_reason = State()


def get_user_management_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Список пользователей", callback_data="list_users")
    builder.button(text="Заблокированные пользователи", callback_data="blocked_users")
    builder.button(text="Заблокировать пользователя", callback_data="block_user")
    builder.button(text="Разблокировать пользователя", callback_data="unblock_user")
    builder.button(text="Статистика пользователей", callback_data="user_statistics")
    builder.button(text="Назад в главное меню", callback_data="back_to_menu")
    builder.adjust(2)
    return builder.as_markup()


@router.callback_query(F.data == "manage_users")
async def show_user_management(callback: CallbackQuery):
    if callback.from_user.id != config.admin_user_id:
        await callback.answer("У вас нет доступа к этой функции.", show_alert=True)
        return

    await message_cleaner.delete_previous_messages(callback.bot, callback.from_user.id)
    response = await callback.message.edit_text("Панель управления пользователями:",
                                                reply_markup=get_user_management_keyboard())
    await message_cleaner.add_message_to_delete(callback.from_user.id, response)


@router.callback_query(F.data == "list_users")
async def list_users(callback: CallbackQuery):
    if callback.from_user.id != config.admin_user_id:
        await callback.answer("У вас нет доступа к этой функции.", show_alert=True)
        return

    users = get_all_users()
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
        await callback.answer("У вас нет доступа к этой функции.", show_alert=True)
        return

    blocked_users = get_blocked_users()
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
        await callback.answer("У вас нет доступа к этой функции.", show_alert=True)
        return

    await callback.message.edit_text("Введите ID пользователя, которого хотите заблокировать:")
    await state.set_state(AdminStates.waiting_for_user_id)


@router.message(StateFilter(AdminStates.waiting_for_user_id))
async def process_user_id_for_block(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите корректный ID пользователя (только цифры).")
        return

    user_id = int(message.text)
    await state.update_data(user_id=user_id)
    await message.answer("Введите причину блокировки:")
    await state.set_state(AdminStates.waiting_for_block_reason)


@router.message(StateFilter(AdminStates.waiting_for_block_reason))
async def process_block_reason(message: Message, state: FSMContext):
    reason = message.text
    user_data = await state.get_data()
    user_id = user_data['user_id']

    block_user(user_id, reason)
    await state.clear()
    await message.answer(f"Пользователь с ID {user_id} заблокирован. Причина: {reason}",
                         reply_markup=get_user_management_keyboard())


@router.callback_query(F.data == "unblock_user")
async def start_unblock_user(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != config.admin_user_id:
        await callback.answer("У вас нет доступа к этой функции.", show_alert=True)
        return

    await callback.message.edit_text("Введите ID пользователя, которого хотите разблокировать:")
    await state.set_state(AdminStates.waiting_for_user_id)


@router.message(StateFilter(AdminStates.waiting_for_user_id))
async def process_user_id_for_unblock(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите корректный ID пользователя (только цифры).")
        return

    user_id = int(message.text)
    unblock_user(user_id)
    await state.clear()
    await message.answer(f"Пользователь с ID {user_id} разблокирован.", reply_markup=get_user_management_keyboard())


@router.callback_query(F.data == "user_statistics")
async def show_user_statistics(callback: CallbackQuery):
    if callback.from_user.id != config.admin_user_id:
        await callback.answer("У вас нет доступа к этой функции.", show_alert=True)
        return

    stats = get_user_statistics()
    stats_text = (
        f"Статистика пользователей:\n\n"
        f"Всего пользователей: {stats['total_users']}\n"
        f"Активных пользователей: {stats['active_users']}\n"
        f"Заблокированных пользователей: {stats['blocked_users']}\n"
        f"Количество созданных сессий: {stats['total_sessions']}\n"
        f"Среднее количество сессий на пользователя: {stats['avg_sessions_per_user']:.2f}"
    )
    await callback.message.edit_text(stats_text, reply_markup=get_user_management_keyboard())