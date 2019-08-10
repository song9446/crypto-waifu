THROUGHPUT=20
TIME_UNIT=0.01
import asyncio
async def wrapper(coru, semaphore, sec):
    async with semaphore:
        r = await coru
        await asyncio.sleep(sec)
        return r
def limited_api(corus, n=THROUGHPUT, sec=TIME_UNIT):
    semaphore = asyncio.Semaphore(n)
    return asyncio.gather(*[wrapper(coru, semaphore, sec) for coru in corus])
import logging
logger = logging.getLogger(__name__)
def log(retry_state):
    if retry_state.attempt_number < 1:
        loglevel = logging.INFO
    else:
        loglevel = logging.WARNING
    logger.log(
        loglevel, 'Retrying %s: attempt %s ended with: %s',
        retry_state.fn, retry_state.attempt_number, retry_state.outcome)

