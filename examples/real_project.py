"""
Example real-world file for testing HezGene evolution.
Contains functions, a class with methods, constants, and imports.
"""

API_KEY = "sk-1234567890"
MAX_RETRIES = 3


def fetch_user_data(user_id: int) -> dict:
    """Fetch user data from the API."""
    result = {"id": user_id, "name": f"User_{user_id}", "status": "active"}
    return result


def process_users(users: list[dict]) -> list[dict]:
    """Process a list of users, filter active ones, sort by name."""
    active = []
    for user in users:
        if user.get("status") == "active":
            active.append(user)
    return sorted(active, key=lambda u: u["name"])


class UserManager:
    """Manages user operations."""

    def __init__(self, db_connection):
        self.db = db_connection
        self.cache = {}

    def get_user(self, user_id: int) -> dict | None:
        """Get user from cache or database."""
        if user_id in self.cache:
            return self.cache[user_id]
        user = self.db.get(user_id)
        if user:
            self.cache[user_id] = user
        return user

    def save_user(self, user_data: dict) -> bool:
        """Save user to database."""
        try:
            self.db[user_data["id"]] = user_data
            return True
        except Exception:
            return False


def calculate_statistics(numbers: list[float]) -> dict[str, float]:
    """Calculate basic statistics for a list of numbers."""
    if not numbers:
        return {"mean": 0.0, "total": 0.0, "count": 0, "min": 0.0, "max": 0.0}

    total = 0.0
    for n in numbers:
        total = total + n

    mean = total / len(numbers)

    min_val = numbers[0]
    max_val = numbers[0]
    for n in numbers:
        if n < min_val:
            min_val = n
        if n > max_val:
            max_val = n

    return {
        "mean": mean,
        "total": total,
        "count": len(numbers),
        "min": min_val,
        "max": max_val,
    }


def main():
    """Main entry point."""
    users = fetch_user_data(123)
    processed = process_users([users])
    print(f"Processed {len(processed)} users")


if __name__ == "__main__":
    main()
