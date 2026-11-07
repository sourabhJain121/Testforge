def compile_payload(code_str: str):
    byte_code = compile(code_str, '<string>', 'exec')
    exec(byte_code)
