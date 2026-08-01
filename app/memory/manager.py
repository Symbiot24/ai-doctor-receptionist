class ConversationManager:

    def __init__(self):
        self.conversations = {}

    def get_messages(self, user_id: int):

        if user_id not in self.conversations:

            self.conversations[user_id] = []

        return self.conversations[user_id]

    def add_message(self, user_id: int, role: str, content: str):

        self.get_messages(user_id).append(
            {
                "role": role,
                "content": content,
            }
        )

    def clear(self, user_id: int):

        self.conversations[user_id] = []