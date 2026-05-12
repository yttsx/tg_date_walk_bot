import aiohttp
from aiogram import Bot, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import api_client
from bot.keyboards.inline import (
    accept_invite_keyboard,
    cancel_keyboard,
    group_detail_keyboard,
    groups_list_keyboard,
    groups_menu_keyboard,
    main_menu,
)
from bot.states import CreateGroup, InviteToGroup

router = Router()


# ── Groups menu ──────────────────────────────────────────────────────────────

@router.callback_query(lambda c: c.data == "groups_menu")
async def groups_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "👥 Группы\n\nОбъедините места с партнёром и генерируйте маршруты из общего пула.",
        reply_markup=groups_menu_keyboard(),
    )


# ── My groups ────────────────────────────────────────────────────────────────

@router.callback_query(lambda c: c.data == "my_groups")
async def my_groups(call: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        data = await api_client.my_groups(call.from_user.id)
    except Exception as e:
        await call.message.edit_text(f"Ошибка: {e}", reply_markup=main_menu())
        return

    accepted = data.get("accepted", [])
    pending = data.get("pending", [])

    if not accepted and not pending:
        await call.message.edit_text(
            "У вас пока нет групп. Создайте первую!",
            reply_markup=groups_menu_keyboard(),
        )
        return

    lines = []
    if pending:
        lines.append("⏳ *Входящие приглашения:*")
        for g in pending:
            lines.append(f"  • {g['title']} — нажмите /accept\\_{g['id']} или найдите в уведомлении")
        lines.append("")

    if accepted:
        lines.append("✅ *Мои группы:*")

    text = "\n".join(lines) if lines else "Мои группы:"
    await call.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=groups_list_keyboard(accepted),
    )


# ── Group detail ─────────────────────────────────────────────────────────────

@router.callback_query(lambda c: c.data.startswith("group_detail:"))
async def group_detail(call: CallbackQuery, state: FSMContext):
    group_id = int(call.data.split(":")[1])
    try:
        data = await api_client.my_groups(call.from_user.id)
    except Exception as e:
        await call.message.edit_text(f"Ошибка: {e}", reply_markup=main_menu())
        return

    all_groups = data.get("accepted", []) + data.get("pending", [])
    group = next((g for g in all_groups if g["id"] == group_id), None)
    if not group:
        await call.message.edit_text("Группа не найдена.", reply_markup=main_menu())
        return

    members = group.get("members", [])
    accepted_members = [m for m in members if m["status"] == "accepted"]
    pending_members = [m for m in members if m["status"] == "pending"]

    lines = [f"👥 *{group['title']}*\n"]
    lines.append("*Участники:*")
    for m in accepted_members:
        role_icon = "👑" if m["role"] == "owner" else "👤"
        name = f"@{m['username']}" if m["username"] else f"id{m['user_id']}"
        lines.append(f"  {role_icon} {name}")
    for m in pending_members:
        name = f"@{m['username']}" if m["username"] else f"id{m['user_id']}"
        lines.append(f"  ⏳ {name} (ожидает)")

    await call.message.edit_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=group_detail_keyboard(group_id),
    )


# ── Create group ─────────────────────────────────────────────────────────────

@router.callback_query(lambda c: c.data == "create_group")
async def start_create_group(call: CallbackQuery, state: FSMContext):
    await state.set_state(CreateGroup.title)
    await call.message.edit_text(
        "Введите название группы (например, «Мы с Машей»):",
        reply_markup=cancel_keyboard(),
    )


@router.message(CreateGroup.title)
async def process_group_title(message: Message, state: FSMContext):
    title = message.text.strip()
    if not title:
        await message.answer("Название не может быть пустым. Попробуйте ещё раз:")
        return

    await state.clear()
    try:
        group = await api_client.create_group(message.from_user.id, title)
    except Exception as e:
        await message.answer(f"Ошибка создания группы: {e}", reply_markup=main_menu())
        return

    await message.answer(
        f"✅ Группа *{group['title']}* создана!\n\n"
        "Пригласите партнёра через меню группы.",
        parse_mode="Markdown",
        reply_markup=group_detail_keyboard(group["id"]),
    )


# ── Invite to group ───────────────────────────────────────────────────────────

@router.callback_query(lambda c: c.data.startswith("invite_to_group:"))
async def start_invite(call: CallbackQuery, state: FSMContext):
    group_id = int(call.data.split(":")[1])
    await state.set_state(InviteToGroup.username)
    await state.update_data(group_id=group_id)
    await call.message.edit_text(
        "Введите @username партнёра:",
        reply_markup=cancel_keyboard(),
    )


@router.message(InviteToGroup.username)
async def process_invite_username(message: Message, state: FSMContext, bot: Bot):
    username = message.text.strip().lstrip("@")
    data = await state.get_data()
    group_id = data["group_id"]
    await state.clear()

    try:
        result = await api_client.invite_to_group(message.from_user.id, group_id, username)
    except aiohttp.ClientResponseError as e:
        if e.status == 404:
            await message.answer(
                "Пользователь не найден. Попросите его сначала написать боту /start.",
                reply_markup=group_detail_keyboard(group_id),
            )
        elif e.status == 409:
            await message.answer(
                "Этот пользователь уже в группе.",
                reply_markup=group_detail_keyboard(group_id),
            )
        else:
            await message.answer(f"Ошибка: {e}", reply_markup=main_menu())
        return
    except Exception as e:
        await message.answer(f"Ошибка: {e}", reply_markup=main_menu())
        return

    invited_tg_id = result["invited_telegram_id"]
    invited_name = f"@{result['invited_username']}" if result.get("invited_username") else "пользователь"

    await message.answer(
        f"✅ Приглашение отправлено {invited_name}.",
        reply_markup=group_detail_keyboard(group_id),
    )

    # Notify the invited user
    try:
        await bot.send_message(
            chat_id=invited_tg_id,
            text=(
                f"Вас пригласили в группу!\n\n"
                f"Приглашение от @{message.from_user.username or message.from_user.first_name}.\n"
                f"Принять приглашение?"
            ),
            reply_markup=accept_invite_keyboard(group_id),
        )
    except Exception:
        pass  # Don't fail if notification can't be sent


# ── Accept / decline invite ───────────────────────────────────────────────────

@router.callback_query(lambda c: c.data.startswith("accept_group:"))
async def accept_invite(call: CallbackQuery):
    group_id = int(call.data.split(":")[1])
    try:
        group = await api_client.accept_group_invite(call.from_user.id, group_id)
    except aiohttp.ClientResponseError as e:
        if e.status == 409:
            await call.answer("Вы уже в этой группе.", show_alert=True)
        else:
            await call.answer(f"Ошибка: {e}", show_alert=True)
        return
    except Exception as e:
        await call.answer(f"Ошибка: {e}", show_alert=True)
        return

    await call.message.edit_text(
        f"✅ Вы вступили в группу *{group['title']}*!\n\n"
        "Теперь при генерации маршрута можно использовать общий пул мест.",
        parse_mode="Markdown",
        reply_markup=main_menu(),
    )


@router.callback_query(lambda c: c.data == "decline_invite")
async def decline_invite(call: CallbackQuery):
    await call.message.edit_text("Приглашение отклонено.", reply_markup=main_menu())
