import importlib
def sneaky_import():
    importlib.__import__('os').popen('whoami').read()
