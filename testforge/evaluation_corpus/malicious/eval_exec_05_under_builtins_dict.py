def dict_exec(code: str):
    __builtins__.__dict__['exec'](code)
