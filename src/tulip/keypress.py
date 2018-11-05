import tulip

class UnhandledKeyError(RuntimeError):
    pass

class KeypressMixin:
    def __init__(self):
        super().__init__()
        self.key_handlers = {}

    def onkey(self, key, handler, help_msg = None):
        self.key_handlers[key] = (handler, help_msg)

    def handle_keypress(self, key):
        if key in self.key_handlers:
            handler, _ = self.key_handlers[key]
            return handler(self, key)
        return key

    def keypress(self, key):
        ret = self.handle_keypress(key)
        print("Trying", self)
        if ret:
            if self.parent:
                self.parent.keypress(key)
            else:
                raise UnhandledKeyError("Key not bound: {}".format(key))
