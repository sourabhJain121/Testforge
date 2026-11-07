import builtins
def sneaky_eval(payload: str):
    return builtins.eval(payload)
