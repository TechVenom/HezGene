def filter_active_users(users: list[dict]) -> list[dict]:
    """
    Filter users to return only active ones.
    This has an unnecessary intermediate variable and verbose loop.
    """
    active_users = []
    for user in users:
        if user.get("status") == "active":
            active_users.append(user)
    return active_users
