import asyncio, httpx, json

async def test_with_chat_api():
    """Test via /api/chat (messages format) avec think=False"""
    payload = {
        'model': 'qwen3:1.7b',
        'messages': [
            {'role': 'system', 'content': 'Tu es un agronome expert.'},
            {'role': 'user', 'content': 'Comment soigner la rouille du haricot? Reponds en 2 phrases.'}
        ],
        'stream': False,
        'think': False,
        'options': {
            'temperature': 0.3,
            'num_predict': 300
        }
    }
    print('Test /api/chat with think=False...')
    async with httpx.AsyncClient(timeout=180) as c:
        r = await c.post('http://localhost:11434/api/chat', json=payload)
        data = r.json()
        msg = data.get('message', {})
        content = msg.get('content', '')
        print('Status:', r.status_code)
        print('Content length:', len(content))
        print('Content:', content[:400])
        print('Duration (s):', round(data.get('total_duration',0)/1e9, 1))

asyncio.run(test_with_chat_api())
