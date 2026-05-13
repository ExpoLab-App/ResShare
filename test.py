from backend.RSDB_kv_service import get_kv, set_kv
print('Testing KV service with same key...')
result = set_kv('test', 'hello world')

print(f'Set result: {result}')
value = get_kv('test')
print(f'Get result: \"{value}\"')