class Chat_histroy:
    def __init__(self, max_history=5):
        self.max_history = max_history
        self.conversations = []

    def add_message(self, message):
        if len(self.conversations) >= self.max_history:
            self.conversations.pop(0)
        self.conversations.append(message)

    def get_messages(self):
        print(self.conversations)
        return self.conversations