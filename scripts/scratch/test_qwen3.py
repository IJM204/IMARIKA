import asyncio, httpx, json

async def main():
    # Test qwen3:1.7b without thinking tags
    payload = {
        'model': 'qwen3:1.7b',
        'prompt': '/no_think Comment soigner la rouille du haricot?',
        'stream': False,
        'options': {
            'temperature': 0.3,
            'num_predict': 200
        }
    }
    print('Sending to qwen3:1.7b...')
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post('http://localhost:11434/api/generate', json=payload)
        data = r.json()
        print('Status:', r.status_code)
        resp = data.get('response', '')
        print('Response length:', len(resp))
        print('Response (first 300 chars):', resp[:300])
        print('Done:', data.get('done'))
        print('Total duration (s):', round(data.get('total_duration',0)/1e9, 1))

asyncio.run(main())
