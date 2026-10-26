import asyncio, sys, httpx
sys.path.insert(0, 'D:/AGRIBurundi-AI')

async def main():
    # 1. Test Ollama direct
    async with httpx.AsyncClient(timeout=5) as c:
        r = await c.get('http://localhost:11434/api/tags')
        data = r.json()
        models = [m['name'] for m in data.get('models', [])]
        print('Models in Ollama:', models)

    # 2. Test backend via the NEW services (not old main.py)
    from backend.services.ollama_service import ollama_service
    print('Configured model in .env:', ollama_service.model)
    print('Model available?', await ollama_service.is_model_available())
    
    # 3. Quick generation test with real model
    real_model = models[0] if models else None
    print('Real model to use:', real_model)
    if real_model:
        payload = {'model': real_model, 'prompt': 'Dis OK', 'stream': False, 'options': {'num_predict': 10}}
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post('http://localhost:11434/api/generate', json=payload)
            resp = r.json()
            print('Generation test response:', resp.get('response', 'EMPTY')[:100])

asyncio.run(main())
