import asyncio

class AIScheduler:
    """Queueing and batching engine to stabilize local Ollama inference."""
    def __init__(self):
        self.queue = asyncio.Queue()
        self.max_concurrent = 2
        
    async def schedule_inference(self, prompt: str):
        await self.queue.put(prompt)
        return "Scheduled"
