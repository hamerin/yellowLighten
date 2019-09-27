class Error(Exception):
    pass


class CommandError(Error):
    def __init__(self, message=None):
        self.message = message
