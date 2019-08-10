THROUGHPUT=100
TIME_UNIT=0.1
import asyncio
async def wrapper(coru, semaphore, sec):
    async with semaphore:
        r = await coru
        await asyncio.sleep(sec)
        return r
def limited_api(corus, n=THROUGHPUT, sec=TIME_UNIT):
    semaphore = asyncio.Semaphore(n)
    return asyncio.gather(*[wrapper(coru, semaphore, sec) for coru in corus])
