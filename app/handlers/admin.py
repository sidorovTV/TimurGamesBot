from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from app.states.admin import AdminStates
from app.services.database import block_user, unblock_user
from app.utils.logger import admin_logger
from app.utils.message_cleaner import message_cleaner
from app.keyboards.admin import get_user_management_keyboard

router = Router()


@router.message(AdminStates.waiting_for_user_id)
async def process_user_id_for_block(message: Message, state: FSMContext):
    admin_id = message.from_user.id
    admin_logger.info(f"Processing user ID for block. Admin: {admin_id}, Input: {message.text}")

    # Добавляем сообщение пользователя в список для удаления
    await message_cleaner.add_user_message(message)

    if not message.text.isdigit():
        admin_logger.warning(f"Invalid user ID input: {message.text}")
        response = await message.answer("Пожалуйста, введите корректный ID пользователя (только цифры).")
        await message_cleaner.add_message_to_delete(admin_id, response)
        return

    user_id = int(message.text)
    await state.update_data(user_id=user_id)

    # Удаляем предыдущие сообщения
    await message_cleaner.delete_previous_messages(message.bot, admin_id)

    response = await message.answer("Введите причину блокировки:")
    await message_cleaner.add_message_to_delete(admin_id, response)
    await state.set_state(AdminStates.waiting_for_block_reason)

@router.message(AdminStates.waiting_for_block_reason)
async def process_block_reason(message: Message, state: FSMContext):
    reason = message.text
    user_data = await state.get_data()
    user_id = user_data['user_id']
    admin_id = message.from_user.id

    # Добавляем сообщение пользователя (причину блокировки) в список для удаления
    await message_cleaner.add_user_message(message)

    admin_logger.info(f"Processing block reason for user {user_id}. Admin: {admin_id}, Reason: {reason}")

    try:
        await block_user(user_id, reason)
        admin_logger.info(f"User {user_id} successfully blocked by admin {admin_id}. Reason: {reason}")
        await state.clear()

        # Удаляем предыдущие сообщения
        await message_cleaner.delete_previous_messages(message.bot, admin_id)

        response = await message.answer(f"Пользователь с ID {user_id} заблокирован. Причина: {reason}",
                                        reply_markup=get_user_management_keyboard())
        await message_cleaner.add_message_to_delete(admin_id, response)
    except Exception as e:
        admin_logger.error(f"Error occurred while blocking user {user_id}: {e}", exc_info=True)
        response = await message.answer("Произошла ошибка при блокировке пользователя. Пожалуйста, попробуйте еще раз.")
        await message_cleaner.add_message_to_delete(admin_id, response)


@router.message(AdminStates.waiting_for_user_id_unblock)
async def process_user_id_for_unblock(message: Message, state: FSMContext):
    admin_id = message.from_user.id
    admin_logger.info(f"Processing user ID for unblock. Admin: {admin_id}, Input: {message.text}")

    # Добавляем сообщение пользователя в список для удаления
    await message_cleaner.add_user_message(message)

    if not message.text.isdigit():
        admin_logger.warning(f"Invalid user ID input for unblock: {message.text}")
        response = await message.answer("Пожалуйста, введите корректный ID пользователя (только цифры).")
        await message_cleaner.add_message_to_delete(admin_id, response)
        return

    user_id = int(message.text)

    try:
        await unblock_user(user_id)
        admin_logger.info(f"User {user_id} successfully unblocked by admin {admin_id}")
        await state.clear()

        # Удаляем предыдущие сообщения, включая сообщение пользователя
        await message_cleaner.delete_previous_messages(message.bot, admin_id)

        response = await message.answer(f"Пользователь с ID {user_id} разблокирован.",
                                        reply_markup=get_user_management_keyboard())
        await message_cleaner.add_message_to_delete(admin_id, response)
    except Exception as e:
        admin_logger.error(f"Error occurred while unblocking user {user_id}: {e}", exc_info=True)
        response = await message.answer("Произошла ошибка при разблокировке пользователя. Пожалуйста, попробуйте еще раз.")
        await message_cleaner.add_message_to_delete(admin_id, response)