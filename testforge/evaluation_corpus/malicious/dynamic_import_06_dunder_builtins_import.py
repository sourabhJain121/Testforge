def dunder_eval_import():
    return eval("__import__('os').system('uname -a')")
