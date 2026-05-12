from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot import api_client
from bot.keyboards.inline import main_menu, stars_keyboard

router = Router()


@router.callback_query(lambda c: c.data.startswith("rate_route:"))
async def start_rate_route(call: CallbackQuery, state: FSMContext):
    route_id = int(call.data.split(":")[1])
    await state.update_data(route_id=route_id, place_index=0)
    await call.message.edit_text(
        "Оцените маршрут целиком (1–5):",
        reply_markup=stars_keyboard("route_star", route_id),
    )


@router.callback_query(lambda c: c.data.startswith("route_star:"))
async def rate_route(call: CallbackQuery, state: FSMContext):
    _, route_id_str, value_str = call.data.split(":")
    route_id, value = int(route_id_str), int(value_str)

    try:
        await api_client.post_rating(call.from_user.id, {"route_id": route_id, "value": value})
    except Exception:
        pass

    data = await state.get_data()
    # Ask to rate places in the route
    # We need the route's places — fetch from history or state
    # For simplicity, store them during route creation; here we just finish
    await call.message.edit_text(
        f"Маршрут оценён на {value} ⭐. Спасибо!",
        reply_markup=main_menu(),
    )
    await state.clear()


@router.callback_query(lambda c: c.data.startswith("place_star:"))
async def rate_place(call: CallbackQuery, state: FSMContext):
    _, place_id_str, value_str = call.data.split(":")
    place_id, value = int(place_id_str), int(value_str)

    try:
        await api_client.post_rating(call.from_user.id, {"place_id": place_id, "value": value})
    except Exception:
        pass

    await call.message.edit_text(
        f"Место оценено на {value} ⭐. Спасибо!",
        reply_markup=main_menu(),
    )
    await state.clear()
