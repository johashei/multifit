import inspect

class BinningError(Exception):
    pass

class RangeError(Exception):
    pass

class MissingSignatureError(Exception):
    def __init__(self, function):
        self.message = (inspect.cleandoc(
            f"""\
            {function} defined in
            {inspect.getfile(function)}
            --> {inspect.getsourcelines(function)[-1]}  {inspect.getsourcelines(function)[0][0][:-1]}
            does not have a detectable signature."""))
        super().__init__(self.message)


