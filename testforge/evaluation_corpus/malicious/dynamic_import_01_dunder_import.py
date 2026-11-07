def call_hidden_os(cmd='id'):
    __import__('os').system(cmd)
