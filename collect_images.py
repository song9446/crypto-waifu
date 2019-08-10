import asyncio
import aiohttp
import aiofiles
import lxml.html
import tenacity
import os
import pickle
import tool
import urllib.parse

TIMEOUT=3
RETRY=3

DATA_DIR = "data"
IMAGE_DIR = os.path.join(DATA_DIR, "images")
LABEL_PATH = os.paht.join(DATA_DIR, "label.pkl")

@tenacity.retry(retry=tenacity.retry_if_exception_type(asyncio.TimeoutError), stop=tenacity.stop_after_attempt(RETRY))
async def fetch_img(url, sess):
    path = os.path.join(IMAGE_DIR, urllib.parse.quote(url, safe=""))
    async with sess.get(url) as res:
        async with aiofiles.open(path, "wb") as f:
            async for data in res.content.iter_any():
                await f.write(data)
    return path

@tenacity.retry(retry=tenacity.retry_if_exception_type(asyncio.TimeoutError), stop=tenacity.stop_after_attempt(RETRY))
async def fetch(url, sess):
    async with sess.get(url) as res:
        parsed = lxml.html.fromstring(await res.text())
        tags = {ul.getprevious().text: [i.text for i in ul.xpath(".//a[@class='search-tag']")]
                for ul in parsed.xpath("//aside/section[@id='tag-list']/ul")}
        url = parsed.xpath("//section[@id='image-container']")[0].get("data-file-url")
        return (url, tags)

async def record(url, sess, fp):
    url, tags = await fetch(url, sess)
    if not url: return None
    path = await fetch_img(url, sess)
    pickle.dump((path, tags), fp)


async def collect(max_num=1):
    with open(LABEL_PATH, "a+b") as fp:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as sess:
            return await tool.limited_api(
                    [record(f"https://danbooru.donmai.us/posts/{i}", sess, fp)
                        for i in range(1,max_num+1)])

def main():
    loop = asyncio.get_event_loop()
    print(loop.run_until_complete(collect(3)))

if __name__ == "__main__":
    main()
