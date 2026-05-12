from aiogram.fsm.state import State, StatesGroup


class AddPlace(StatesGroup):
    title = State()
    address = State()
    url = State()
    tags = State()
    group_choice = State()


class CreateGroup(StatesGroup):
    title = State()


class InviteToGroup(StatesGroup):
    username = State()


class CreateRoute(StatesGroup):
    choose_scenario = State()


class RateRoute(StatesGroup):
    route_stars = State()
    place_stars = State()
    place_index = State()
