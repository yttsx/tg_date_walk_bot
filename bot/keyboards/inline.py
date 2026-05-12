from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить место", callback_data="add_place")],
        [InlineKeyboardButton(text="🗺 Создать маршрут", callback_data="create_route")],
        [InlineKeyboardButton(text="🎲 Случайное место", callback_data="random_place")],
        [InlineKeyboardButton(text="📋 Мои места", callback_data="my_places")],
        [InlineKeyboardButton(text="👥 Группы", callback_data="groups_menu")],
        [InlineKeyboardButton(text="🕒 История маршрутов", callback_data="history")],
    ])


def scenario_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💑 Свидание (2 чел.)", callback_data="scenario:date")],
        [InlineKeyboardButton(text="🚶 Прогулка (3+ чел.)", callback_data="scenario:walk")],
        [InlineKeyboardButton(text="🌤 Лёгкая прогулка", callback_data="scenario:light")],
        [InlineKeyboardButton(text="← Назад", callback_data="back_to_menu")],
    ])


def route_mode_keyboard(groups: list[dict]) -> InlineKeyboardMarkup:
    """Ask user: solo or with which group."""
    rows = [
        [InlineKeyboardButton(text="👤 Только мои места", callback_data="route_mode:0")],
    ]
    for g in groups[:5]:
        rows.append([
            InlineKeyboardButton(
                text=f"👥 {g['title']}",
                callback_data=f"route_mode:{g['id']}",
            )
        ])
    rows.append([InlineKeyboardButton(text="← Назад", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def route_actions(route_id: int, scenario: str, group_id: int = 0) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(
            text="🔄 Перегенерировать",
            callback_data=f"reroll:{route_id}:{scenario}:{group_id}",
        )],
    ]
    if group_id:
        rows.append([InlineKeyboardButton(
            text="🚨 Уведомить участников",
            callback_data=f"notify_group:{route_id}:{group_id}",
        )])
    rows.append([InlineKeyboardButton(text="⭐ Оценить маршрут", callback_data=f"rate_route:{route_id}")])
    rows.append([InlineKeyboardButton(text="← В меню", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def stars_keyboard(prefix: str, entity_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=str(i), callback_data=f"{prefix}:{entity_id}:{i}")
            for i in range(1, 6)
        ]
    ])


def tag_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="☕ Кафе", callback_data="set_tag:cafe"),
            InlineKeyboardButton(text="🏞️ Парк", callback_data="set_tag:park"),
            InlineKeyboardButton(text="🍴 Еда", callback_data="set_tag:food"),
        ],
        [InlineKeyboardButton(text="Отмена", callback_data="cancel")],
    ])


def skip_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пропустить", callback_data="skip_url")],
        [InlineKeyboardButton(text="Отмена", callback_data="cancel")],
    ])


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data="cancel")],
    ])


def random_place_actions() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Другое место", callback_data="random_place")],
        [InlineKeyboardButton(text="← В меню", callback_data="back_to_menu")],
    ])


def places_list_keyboard(places: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for p in places[:20]:
        rows.append([
            InlineKeyboardButton(text=f"🗑 {p['title']}", callback_data=f"delete_place:{p['id']}"),
        ])
    rows.append([InlineKeyboardButton(text="← Назад", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_delete_keyboard(place_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete:{place_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="my_places"),
        ]
    ])


def place_group_keyboard(groups: list[dict]) -> InlineKeyboardMarkup:
    """Ask which group a new place belongs to (or private)."""
    rows = [
        [InlineKeyboardButton(text="🔒 Только мои маршруты", callback_data="place_group:0")],
    ]
    for g in groups[:8]:
        rows.append([
            InlineKeyboardButton(
                text=f"👥 {g['title']}",
                callback_data=f"place_group:{g['id']}",
            )
        ])
    rows.append([InlineKeyboardButton(text="Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# --- Group keyboards ---

def groups_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать группу", callback_data="create_group")],
        [InlineKeyboardButton(text="📋 Мои группы", callback_data="my_groups")],
        [InlineKeyboardButton(text="← Назад", callback_data="back_to_menu")],
    ])


def groups_list_keyboard(groups: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for g in groups[:10]:
        member_count = len(g.get("members", []))
        rows.append([
            InlineKeyboardButton(
                text=f"👥 {g['title']} ({member_count} уч.)",
                callback_data=f"group_detail:{g['id']}",
            )
        ])
    rows.append([InlineKeyboardButton(text="← Назад", callback_data="groups_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def group_detail_keyboard(group_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Пригласить", callback_data=f"invite_to_group:{group_id}")],
        [InlineKeyboardButton(text="← К группам", callback_data="my_groups")],
    ])


def route_notification_keyboard(route_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Пройден", callback_data=f"route_done:{route_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"route_decline:{route_id}"),
        ]
    ])


def accept_invite_keyboard(group_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_group:{group_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data="decline_invite"),
        ]
    ])
