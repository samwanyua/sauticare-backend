import sys
from api.services.asr_service import asr_service
import asyncio

async def test():
    try:
        text, metrics = await asr_service.transcribe_with_model(sys.argv[1])
        print("Transcription:", text)
    except Exception as e:
        print("Error:", e)

asyncio.run(test())
