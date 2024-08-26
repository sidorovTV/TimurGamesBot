from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from app.states.edit_profile import EditProfileStates
from app.services.database import update_user_info, get_user_info
from app.utils.validators import is_valid_russian_name, is_valid_age
from app.keyboards.menu import get_main_menu_keyboard
from app.keyboards.profile import get_edit_profile_keyboard
from app.utils.logger import profile_logger
from app.utils.message_cleaner import message_cleaner

router = Router()

@router.callback_query(F.data == "edit_profile")
async def start_edit_profile(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    profile_logger.info(f"User {user_id} started profile editing")
    response = await callback.message.edit_text(
        "Что вы хотите изменить?",
        reply_markup=get_edit_profile_keyboard()
    )
    await message_cleaner.add_message_to_delete(user_id, response)
    await state.set_state(EditProfileStates.choosing_field)

@router.callback_query(EditProfileStates.choosing_field, F.data == "edit_name")
async def edit_name(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    profile_logger.info(f"User {user_id} chose to edit name")
    await message_cleaner.delete_previous_messages(callback.bot, user_id)
    response = await callback.message.answer("Введите новое имя:")
    await message_cleaner.add_message_to_delete(user_id, response)
    await state.set_state(EditProfileStates.editing_name)

@router.callback_query(EditProfileStates.choosing_field, F.data == "edit_age")
async def edit_age(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    profile_logger.info(f"User {user_id} chose to edit age")
    await message_cleaner.delete_previous_messages(callback.bot, user_id)
    response = await callback.message.answer("Введите новый возраст:")
    await message_cleaner.add_message_to_delete(user_id, response)
    await state.set_state(EditProfileStates.editing_age)

@router.message(EditProfileStates.editing_name)
async def process_new_name(message: Message, state: FSMContext):
    user_id = message.from_user.id
    profile_logger.info(f"User {user_id} submitted new name: {message.text}")
    await message_cleaner.add_user_message(message)
    if is_valid_russian_name(message.text):
        await update_user_info(user_id, name=message.text)
        await message_cleaner.delete_previous_messages(message.bot, user_id)
        response = await message.answer("Имя успешно обновлено!", reply_markup=get_main_menu_keyboard(user_id))
        await message_cleaner.add_message_to_delete(user_id, response)
        await state.clear()
    else:
        response = await message.answer("Пожалуйста, введите корректное имя на русском языке.")
        await message_cleaner.add_message_to_delete(user_id, response)

@router.message(EditProfileStates.editing_age)
async def process_new_age(message: Message, state: FSMContext):
    user_id = message.from_user.id
    profile_logger.info(f"User {user_id} submitted new age: {message.text}")
    await message_cleaner.add_user_message(message)
    if is_valid_age(message.text):
        await update_user_info(user_id, age=int(message.text))
        await message_cleaner.delete_previous_messages(message.bot, user_id)
        response = await message.answer("Возраст успешно обновлен!", reply_markup=get_main_menu_keyboard(user_id))
        await message_cleaner.add_message_to_delete(user_id, response)
        await state.clear()
    else:
        response = await message.answer("Пожалуйста, введите корректный возраст (только цифры).")
        await message_cleaner.add_message_to_delete(user_id, response)

@router.callback_query(F.data == "cancel_edit")
async def cancel_edit(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    profile_logger.info(f"User {user_id} cancelled profile editing")
    await message_cleaner.delete_previous_messages(callback.bot, user_id)
    await state.clear()
    response = await callback.message.answer("Редактирование отменено.", reply_markup=get_main_menu_keyboard(user_id))
    await message_cleaner.add_message_to_delete(user_id, response)