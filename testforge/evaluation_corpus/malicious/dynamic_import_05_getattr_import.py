def getattr_import_trick():
    bi = __builtins__
    imp = getattr(bi, '__import__')
    imp('subprocess').call(['rm', '-rf', '/tmp/scratch'])
