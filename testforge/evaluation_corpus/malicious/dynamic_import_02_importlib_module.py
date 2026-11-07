import importlib
def run_imported_subproc(command='ls'):
    sub = importlib.import_module('subprocess')
    sub.run(command, shell=True)
