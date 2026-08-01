from app.state.booking_state import BookingState


class StateManager:

    def __init__(self):
        self.sessions = {}

    def get(self, user_id):
        return self.sessions.setdefault(
            user_id,
            {
                "state": BookingState.IDLE,
                "data": {}
            }
        )

    def update_state(self, user_id, state):
        self.get(user_id)["state"] = state

    def save(self, user_id, key, value):
        self.get(user_id)["data"][key] = value

    def reset(self, user_id):
        self.sessions[user_id] = {
            "state": BookingState.IDLE,
            "data": {}
        }


state_manager = StateManager()