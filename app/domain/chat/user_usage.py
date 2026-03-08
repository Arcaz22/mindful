class UserUsageEntity:
    def __init__(self, user_id: str, chat_count: int, last_accessed):
        self.user_id = user_id
        self.chat_count = chat_count
        self.last_accessed = last_accessed
