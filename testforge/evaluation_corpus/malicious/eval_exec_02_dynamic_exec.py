def run_dynamic_plugin(plugin_code: str):
    exec(plugin_code, {'__builtins__': None})
