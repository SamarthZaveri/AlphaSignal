import sys
sys.path.insert(0, '.')
import asyncio
from app.scheduler import run_retrain
asyncio.run(run_retrain())
print('Training complete')
