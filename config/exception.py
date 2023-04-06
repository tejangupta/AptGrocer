class CustomError(Exception):
    def __init__(self, error, code, message):
        self.error = error
        self.code = code
        self.message = message
