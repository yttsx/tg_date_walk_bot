import asyncio
import random

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import api_client
from bot.keyboards.inline import (
    cancel_keyboard,
    confirm_delete_keyboard,
    main_menu,
    place_group_keyboard,
    places_list_keyboard,
    random_place_actions,
    skip_keyboard,
    tag_keyboard,
)
from bot.states import AddPlace

router = Router()

TAG_LABELS = {
    "cafe": "☕ Кафе",
    "park": "🏞️ Парк",
    "food": "🍴 Еда",
}


# ── Add place flow ────────────────────────────────────────────────────────────

@router.callback_query(lambda c: c.data == "add_place")
async def start_add_place(call: CallbackQuery, state: FSMContext):
    await state.set_state(AddPlace.title)
    await call.message.edit_text(
        "Введите название места:\n_(например: Кофемания на Патриках)_",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard(),
    )


@router.message(AddPlace.title)
async def got_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AddPlace.address)
    await message.answer(
        "Введите адрес:\n_(например: ул. Малая Бронная, 28)_",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard(),
    )


@router.message(AddPlace.address)
async def got_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    await state.set_state(AddPlace.url)
    await message.answer(
        "Ссылка на место — сайт, 2GIS, Instagram\n_(или пропустите)_",
        parse_mode="Markdown",
        reply_markup=skip_keyboard(),
    )


@router.callback_query(lambda c: c.data == "skip_url", AddPlace.url)
async def skip_url(call: CallbackQuery, state: FSMContext):
    await state.update_data(url=None)
    await state.set_state(AddPlace.tags)
    await call.message.edit_text(
        "Выберите категорию места:",
        reply_markup=tag_keyboard(),
    )


@router.message(AddPlace.url)
async def got_url(message: Message, state: FSMContext):
    await state.update_data(url=message.text.strip())
    await state.set_state(AddPlace.tags)
    await message.answer(
        "Выберите категорию места:",
        reply_markup=tag_keyboard(),
    )


@router.callback_query(lambda c: c.data.startswith("set_tag:"), AddPlace.tags)
async def got_tag(call: CallbackQuery, state: FSMContext):
    tag = call.data.split(":")[1]  # cafe | park | food
    await state.update_data(tag=tag)
    await state.set_state(AddPlace.group_choice)

    # Fetch user's accepted groups to offer group selection
    try:
        groups_data = await api_client.my_groups(call.from_user.id)
        accepted_groups = groups_data.get("accepted", [])
    except Exception:
        accepted_groups = []

    if accepted_groups:
        await call.message.edit_text(
            "В какую группу добавить место?\n\n"
            "🔒 — место попадёт только в ваши личные маршруты.\n"
            "👥 — место будет доступно при генерации маршрута для выбранной группы.",
            reply_markup=place_group_keyboard(accepted_groups),
        )
    else:
        # No groups — save immediately as private
        await _save_place(call, state, group_id=None)


async def _save_place(
    call: CallbackQuery,
    state: FSMContext,
    group_id: int | None,
    group_title: str | None = None,
):
    data = await state.get_data()
    await state.clear()
    tag = data["tag"]
    try:
        place = await api_client.add_place(
            call.from_user.id,
            {
                "title": data["title"],
                "address": data["address"],
                "url": data.get("url"),
                "tags": [tag],
                "group_id": group_id,
            },
        )
        label = TAG_LABELS.get(tag, tag)
        group_line = f"\nДоступно в группе: 👥 {group_title}" if group_id and group_title else ""
        await call.message.edit_text(
            f"✅ Место сохранено!\n\n"
            f"*{place['title']}*\n"
            f"📍 {place['address']}\n"
            f"Категория: {label}{group_line}",
            parse_mode="Markdown",
            reply_markup=main_menu(),
        )
    except Exception as e:
        await call.message.edit_text(f"Ошибка сохранения: {e}", reply_markup=main_menu())


@router.callback_query(lambda c: c.data.startswith("place_group:"), AddPlace.group_choice)
async def got_place_group(call: CallbackQuery, state: FSMContext):
    group_id_str = call.data.split(":")[1]
    group_id = int(group_id_str) if group_id_str != "0" else None

    # Resolve group title for confirmation message
    group_title = None
    if group_id:
        try:
            groups_data = await api_client.my_groups(call.from_user.id)
            all_groups = groups_data.get("accepted", [])
            found = next((g for g in all_groups if g["id"] == group_id), None)
            group_title = found["title"] if found else None
        except Exception:
            pass

    await _save_place(call, state, group_id, group_title)


# ── My places + delete flow ───────────────────────────────────────────────────

@router.callback_query(lambda c: c.data == "my_places")
async def my_places(call: CallbackQuery):
    try:
        places, groups_data = await asyncio.gather(
            api_client.list_places(call.from_user.id),
            api_client.my_groups(call.from_user.id),
        )
    except Exception as e:
        await call.message.edit_text(f"Ошибка: {e}", reply_markup=main_menu())
        return

    if not places:
        await call.message.edit_text(
            "У вас пока нет мест. Добавьте первое!",
            reply_markup=main_menu(),
        )
        return

    group_map = {g["id"]: g["title"] for g in groups_data.get("accepted", [])}

    lines = []
    for p in places[:20]:
        tag = p.get("tags", [])
        label = TAG_LABELS.get(tag[0], tag[0]) if tag else "—"
        group_id = p.get("group_id")
        group_suffix = f"  |  👥 {group_map.get(group_id, '?')}" if group_id else ""
        lines.append(f"• *{p['title']}*\n  📍 {p['address']}  |  {label}{group_suffix}")

    text = "Ваши места (нажмите 🗑 чтобы удалить):\n\n" + "\n\n".join(lines)
    if len(places) > 20:
        text += f"\n\n_...и ещё {len(places) - 20}_"

    await call.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=places_list_keyboard(places),
    )


@router.callback_query(lambda c: c.data.startswith("delete_place:"))
async def ask_confirm_delete(call: CallbackQuery):
    place_id = int(call.data.split(":")[1])
    await call.message.edit_text(
        "Удалить это место? Оно больше не будет появляться в маршрутах.",
        reply_markup=confirm_delete_keyboard(place_id),
    )


@router.callback_query(lambda c: c.data.startswith("confirm_delete:"))
async def confirm_delete(call: CallbackQuery):
    place_id = int(call.data.split(":")[1])
    try:
        await api_client.delete_place(call.from_user.id, place_id)
        await call.answer("Место удалено.", show_alert=False)
    except Exception as e:
        await call.answer(f"Ошибка: {e}", show_alert=True)
        return

    try:
        places = await api_client.list_places(call.from_user.id)
    except Exception:
        await call.message.edit_text("Место удалено.", reply_markup=main_menu())
        return

    if not places:
        await call.message.edit_text("Список пуст. Добавьте новые места!", reply_markup=main_menu())
        return

    lines = []
    for p in places[:20]:
        tag = p.get("tags", [])
        label = TAG_LABELS.get(tag[0], tag[0]) if tag else "—"
        lines.append(f"• *{p['title']}*\n  📍 {p['address']}  |  {label}")

    await call.message.edit_text(
        "Ваши места (нажмите 🗑 чтобы удалить):\n\n" + "\n\n".join(lines),
        parse_mode="Markdown",
        reply_markup=places_list_keyboard(places),
    )


# ── Random place ──────────────────────────────────────────────────────────────

@router.callback_query(lambda c: c.data == "random_place")
async def random_place(call: CallbackQuery):
    try:
        places = await api_client.list_places(call.from_user.id)
    except Exception as e:
        await call.message.edit_text(f"Ошибка: {e}", reply_markup=main_menu())
        return

    if not places:
        await call.message.edit_text(
            "У вас пока нет мест. Добавьте хотя бы одно!",
            reply_markup=main_menu(),
        )
        return

    p = random.choice(places)
    tag = p.get("tags", [])
    label = TAG_LABELS.get(tag[0], tag[0]) if tag else "—"
    url_line = f"\n🔗 {p['url']}" if p.get("url") else ""

    await call.message.edit_text(
        f"🎲 *Случайное место из вашего бэклога:*\n\n"
        f"*{p['title']}*\n"
        f"📍 {p['address']}\n"
        f"Категория: {label}"
        f"{url_line}",
        parse_mode="Markdown",
        disable_web_page_preview=True,
        reply_markup=random_place_actions(),
    )
