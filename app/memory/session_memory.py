from app.state.state_manager import state_manager


class SessionMemory:
    """Utility class for persisting conversation entities.

    The memory lives per user and is cleared when a booking flow finishes or
    is cancelled. It mirrors the ``data`` dict used by ``StateManager`` but offers
    explicit helper methods.
    """

    def save(self, user_id: int, key: str, value):
        """Store a single key/value pair for the given user."""
        state_manager.save(user_id, key, value)

    def get(self, user_id: int):
        """Return the full memory dict for the user (may be empty)."""
        return state_manager.get(user_id)["data"]

    def update(self, user_id: int, data: dict):
        """Merge a dict of values into the user's memory."""
        for k, v in data.items():
            self.save(user_id, k, v)

    def clear(self, user_id: int):
        """Remove all stored entities for the user."""
        # Reset the ``data`` portion while preserving the current state.
        state_manager.get(user_id)["data"] = {}


# Singleton instance used throughout the codebase
session_memory = SessionMemory()
