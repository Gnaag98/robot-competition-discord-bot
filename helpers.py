from discord import CategoryChannel, Guild, Role


def get_role_by_name(guild: Guild, name: str) -> Role|None:
    return next(
        (role for role in guild.roles if role.name == name),
        None)


def get_first_role_by_prefix(
    guild: Guild, prefix: str, ignored_role: Role|None = None
) -> Role|None:
    return next(
        (role for role in guild.roles
            if role.name.startswith(prefix) and role != ignored_role),
        None)


def get_category_by_name(guild: Guild, name: str) -> CategoryChannel|None:
    return next(
        (category for category in guild.categories if category.name == name),
        None)

def get_first_category_by_prefix(
    guild: Guild, prefix: str, ignored_category: CategoryChannel|None = None
) -> CategoryChannel|None:
    return next(
        (category for category in guild.categories
            if category.name.startswith(prefix) and category != ignored_category),
        None)
