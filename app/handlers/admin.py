from aiogram import Router
from aiogram.types import Message
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from app.states.admin import AdminStates
from app.services.database import block_user, unblock_user
from app.keyboards.admin import get_user_management_keyboard

router = Router()


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

    await block_user(user_id, reason)
    await state.clear()
    await message.answer(f"Пользователь с ID {user_id} заблокирован. Причина: {reason}",
                         reply_markup=get_user_management_keyboard())


@router.message(StateFilter(AdminStates.waiting_for_user_id_unblock))
async def process_user_id_for_unblock(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите корректный ID пользователя (только цифры).")
        return

    user_id = int(message.text)
    await unblock_user(user_id)
    await state.clear()
    await message.answer(f"Пользователь с ID {user_id} разблокирован.",
                         reply_markup=get_user_management_keyboard())
