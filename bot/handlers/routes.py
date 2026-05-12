from aiogram import Bot, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot import api_client
from bot.keyboards.inline import (
    main_menu,
    route_accepted_keyboard,
    route_actions,
    route_mode_keyboard,
    route_notification_keyboard,
    route_notify_rate_keyboard,
    scenario_keyboard,
)
from bot.states import CreateRoute

router = Router()


def _format_route(route: dict) -> str:
    lines = ["*Ваш маршрут:*\n"]
    for i, place in enumerate(route["places_json"], 1):
        url_part = f"\n  🔗 {place['url']}" if place.get("url") else ""
        lines.append(f"{i}. *{place['title']}*\n  📍 {place['address']}{url_part}")
    lines.append(
        f"\n⏱ ~{route['total_minutes']} мин | 🚶 {route['walk_minutes']} мин ходьбы"
        f" | 📏 {route.get('distance_m', 0)} м"
    )
    lines.append(f"\n🗺 [Маршрут на Яндекс Картах]({route['yandex_url']})")
    return "\n".join(lines)


def _format_notification(route: dict, sender_name: str, group_title: str) -> str:
    lines = [f"👥 *{sender_name}* поделился маршрутом для группы *{group_title}*:\n"]
    for i, place in enumerate(route["places_json"], 1):
        url_part = f"\n  🔗 {place['url']}" if place.get("url") else ""
        lines.append(f"{i}. *{place['title']}*\n  📍 {place['address']}{url_part}")
    lines.append(
        f"\n⏱ ~{route['total_minutes']} мин | 🚶 {route['walk_minutes']} мин ходьбы"
        f" | 📏 {route.get('distance_m', 0)} м"
    )
    lines.append(f"\n🗺 [Маршрут на Яндекс Картах]({route['yandex_url']})")
    return "\n".join(lines)


# ── Route creation flow ───────────────────────────────────────────────────────

@router.callback_query(lambda c: c.data == "create_route")
async def start_create_route(call: CallbackQuery, state: FSMContext):
    await state.clear()

    try:
        groups_data = await api_client.my_groups(call.from_user.id)
        accepted_groups = groups_data.get("accepted", [])
    except Exception:
        accepted_groups = []

    if accepted_groups:
        await call.message.edit_text(
            "Генерировать маршрут из своих мест или из общего пула группы?",
            reply_markup=route_mode_keyboard(accepted_groups),
        )
    else:
        await state.set_state(CreateRoute.choose_scenario)
        await state.update_data(group_id=None)
        await call.message.edit_text("Выберите сценарий:", reply_markup=scenario_keyboard())


@router.callback_query(lambda c: c.data.startswith("route_mode:"))
async def choose_route_mode(call: CallbackQuery, state: FSMContext):
    group_id_str = call.data.split(":")[1]
    group_id = int(group_id_str) if group_id_str != "0" else None

    await state.set_state(CreateRoute.choose_scenario)
    await state.update_data(group_id=group_id)
    await call.message.edit_text("Выберите сценарий:", reply_markup=scenario_keyboard())


@router.callback_query(lambda c: c.data.startswith("scenario:"))
async def choose_scenario(call: CallbackQuery, state: FSMContext):
    scenario = call.data.split(":")[1]
    data = await state.get_data()
    group_id: int | None = data.get("group_id")
    await state.clear()

    await call.message.edit_text("Генерирую маршрут...")

    try:
        route = await api_client.generate_route(call.from_user.id, scenario, group_id)
    except Exception as e:
        msg = str(e)
        if "422" in msg or "Could not" in msg:
            await call.message.edit_text(
                "Не удалось собрать маршрут. Добавьте больше мест с разными тегами.",
                reply_markup=main_menu(),
            )
        else:
            await call.message.edit_text(f"Ошибка: {e}", reply_markup=main_menu())
        return

    await call.message.edit_text(
        _format_route(route),
        parse_mode="Markdown",
        disable_web_page_preview=True,
        reply_markup=route_actions(route["id"], scenario, group_id or 0),
    )


@router.callback_query(lambda c: c.data.startswith("reroll:"))
async def reroll(call: CallbackQuery):
    parts = call.data.split(":")
    route_id = int(parts[1])
    scenario = parts[2]
    group_id = int(parts[3]) if len(parts) > 3 and parts[3] != "0" else None

    await call.message.edit_text("Перегенерирую...")

    try:
        route = await api_client.reroll_route(call.from_user.id, route_id, scenario, group_id)
    except Exception as e:
        await call.message.edit_text(f"Не удалось: {e}", reply_markup=main_menu())
        return

    await call.message.edit_text(
        _format_route(route),
        parse_mode="Markdown",
        disable_web_page_preview=True,
        reply_markup=route_actions(route["id"], scenario, group_id or 0),
    )


# ── Notify group members ──────────────────────────────────────────────────────

@router.callback_query(lambda c: c.data.startswith("notify_group:"))
async def notify_group(call: CallbackQuery, bot: Bot):
    _, route_id_str, group_id_str = call.data.split(":")
    route_id = int(route_id_str)
    group_id = int(group_id_str)

    # Fetch route and group members in parallel
    try:
        route, groups_data = await _fetch_route_and_groups(call.from_user.id, route_id)
    except Exception as e:
        await call.answer(f"Ошибка: {e}", show_alert=True)
        return

    # Find the group and collect recipients
    group_title = "группы"
    recipients: list[int] = []
    for g in groups_data.get("accepted", []):
        if g["id"] == group_id:
            group_title = g["title"]
            recipients = [
                m["telegram_id"]
                for m in g.get("members", [])
                if m["status"] == "accepted" and m["telegram_id"] != call.from_user.id
            ]
            break

    if not recipients:
        await call.answer("Нет участников для уведомления.", show_alert=True)
        return

    sender_name = call.from_user.username or call.from_user.first_name
    text = _format_notification(route, sender_name, group_title)

    sent = 0
    for tid in recipients:
        try:
            await bot.send_message(
                chat_id=tid,
                text=text,
                parse_mode="Markdown",
                disable_web_page_preview=True,
                reply_markup=route_notification_keyboard(route_id, call.from_user.id),
            )
            sent += 1
        except Exception:
            pass  # member may have blocked the bot

    result = (
        f"✅ Маршрут отправлен всем {sent} участникам группы {group_title}."
        if sent == len(recipients)
        else f"✅ Отправлено {sent} из {len(recipients)} участников."
    )
    await call.answer(result, show_alert=True)


async def _fetch_route_and_groups(telegram_id: int, route_id: int) -> tuple[dict, dict]:
    import asyncio
    route, groups_data = await asyncio.gather(
        api_client.get_route(telegram_id, route_id),
        api_client.my_groups(telegram_id),
    )
    return route, groups_data


# ── Notification response buttons ────────────────────────────────────────────

@router.callback_query(lambda c: c.data.startswith("route_join:"))
async def route_join(call: CallbackQuery, bot: Bot):
    parts = call.data.split(":")
    route_id = int(parts[1])
    creator_id = int(parts[2]) if len(parts) > 2 and parts[2] else 0

    await call.message.edit_reply_markup(reply_markup=route_accepted_keyboard(route_id))
    await call.answer("Отлично! Удачной прогулки! 🚶")

    if creator_id and creator_id != call.from_user.id:
        username = call.from_user.username
        name = f"@{username}" if username else call.from_user.first_name
        try:
            await bot.send_message(
                chat_id=creator_id,
                text=f"🚶 {name} хочет с вами погулять!",
            )
        except Exception:
            pass


@router.callback_query(lambda c: c.data.startswith("route_done:"))
async def route_done(call: CallbackQuery):
    route_id = int(call.data.split(":")[1])
    await call.message.edit_reply_markup(reply_markup=route_notify_rate_keyboard(route_id))
    await call.answer("Оцените маршрут! ⭐")


@router.callback_query(lambda c: c.data.startswith("notify_rate:"))
async def notify_rate(call: CallbackQuery):
    parts = call.data.split(":")
    route_id, value = int(parts[1]), int(parts[2])

    try:
        await api_client.post_rating(call.from_user.id, {"route_id": route_id, "value": value})
    except Exception:
        pass

    try:
        await call.message.delete()
    except Exception:
        await call.message.edit_reply_markup(reply_markup=None)
    await call.answer(f"Маршрут оценён на {value} {'⭐' * value}. Спасибо!", show_alert=True)


@router.callback_query(lambda c: c.data.startswith("route_decline:"))
async def route_declined(call: CallbackQuery, bot: Bot):
    parts = call.data.split(":")
    creator_id = int(parts[2]) if len(parts) > 2 and parts[2] else 0

    try:
        await call.message.delete()
    except Exception:
        await call.message.edit_reply_markup(reply_markup=None)
    await call.answer("Маршрут отклонён")

    if creator_id and creator_id != call.from_user.id:
        username = call.from_user.username
        name = f"@{username}" if username else call.from_user.first_name
        try:
            await bot.send_message(
                chat_id=creator_id,
                text=f"😔 К сожалению, {name} отказался идти по этому маршруту.",
            )
        except Exception:
            pass


# ── History ───────────────────────────────────────────────────────────────────

@router.callback_query(lambda c: c.data == "history")
async def show_history(call: CallbackQuery):
    try:
        routes = await api_client.get_history(call.from_user.id)
    except Exception as e:
        await call.message.edit_text(f"Ошибка: {e}", reply_markup=main_menu())
        return

    if not routes:
        await call.message.edit_text(
            "Маршрутов пока нет. Создайте первый!",
            reply_markup=main_menu(),
        )
        return

    lines = ["*История маршрутов:*\n"]
    for r in routes[:10]:
        places = r.get("places_json", [])
        names = " → ".join(p["title"] for p in places)
        rating = f"⭐ {r['rating_avg']}" if r["rating_avg"] else ""
        lines.append(f"• {names} {rating}")

    await call.message.edit_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=main_menu(),
    )
