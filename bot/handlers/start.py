from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import api_client
from bot.keyboards.inline import main_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, command: CommandObject):
    await state.clear()
    await api_client.auth_user(message.from_user.id, message.from_user.username)

    # Deep link: /start join_<group_id>
    if command.args and command.args.startswith("join_"):
        try:
            group_id = int(command.args.split("_", 1)[1])
            group = await api_client.join_group_by_link(message.from_user.id, group_id)
            await message.answer(
                f"✅ Вы вступили в группу *{group['title']}*!\n\n"
                "Теперь при генерации маршрута можно использовать общий пул мест.",
                parse_mode="Markdown",
                reply_markup=main_menu(),
            )
            return
        except Exception as e:
            await message.answer(
                f"Не удалось вступить в группу: {e}",
                reply_markup=main_menu(),
            )
            return

    await message.answer(
        "Привет! Я помогу вам составить маршрут для прогулки по Москве.\n\n"
        "Добавьте свои любимые места, а я сгенерирую маршрут на 3 остановки.",
        reply_markup=main_menu(),
    )


@router.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "Главное меню:",
        reply_markup=main_menu(),
    )


@router.callback_query(lambda c: c.data == "cancel")
async def cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("Отменено.", reply_markup=main_menu())
