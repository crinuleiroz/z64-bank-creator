# App/Common/AppExceptions.py

class InvalidGameException(Exception):
    default_message = (
        "Invalid game '{game}'. "
        "Sample addresses ar not guaranteed to work with the bank's intended game."
    )

    def __init__(self, game=None, message=None):
        if message is None:
            message = self.default_message.format(game=game)
        super().__init__(message)