import asyncio
import aiohttp
import aiofiles
import lxml.html
import tenacity
import os
import pickle
import socket
import tool
import urllib.parse

TIMEOUT=3
RETRY=10

DATA_DIR = "data"
IMAGE_DIR = os.path.join(DATA_DIR, "images")
LABEL_PATH = os.path.join(DATA_DIR, "label.pkl")

@tenacity.retry(before_sleep=tool.log, stop=tenacity.stop_after_attempt(RETRY))
async def fetch_img(url, sess):
    path = os.path.join(IMAGE_DIR, urllib.parse.quote(url, safe=""))
    async with sess.get(url) as res:
        async with aiofiles.open(path, "wb") as f:
            async for data in res.content.iter_any():
                await f.write(data)
    return path

#@tenacity.retry(retry=(tenacity.retry_if_exception_type(asyncio.TimeoutError) | tenacity.retry_if_exception_type(aiohttp.ClientResponseError)), stop=tenacity.stop_after_attempt(RETRY))
@tenacity.retry(before_sleep=tool.log, stop=tenacity.stop_after_attempt(RETRY))
async def fetch(url, sess):
    async with sess.get(url) as res:
        r = await res.text()
        parsed = lxml.html.fromstring(r)
        title = parsed.xpath("//title")
        if title and title[0].text and title[0].text.startswith("429"):
            raise aiohttp.ClientResponseError
        tags = {ul.getprevious().text: [i.text for i in ul.xpath(".//a[@class='search-tag']")]
                for ul in parsed.xpath("//aside/section[@id='tag-list']/ul")}
        cont = parsed.xpath("//section[@id='image-container']")
        url = cont and cont[0].get("data-file-url")
        return (url, tags)

async def record(url, sess, fp):
    try:
        print(url)
        url, tags = await fetch(url, sess)
        if not url: return None
        path = await fetch_img(url, sess)
        pickle.dump((path, tags), fp)
    except Exception as e:
        raise(e)
        print(e, url)


async def collect(max_num=1, last_num=0):
    conn = aiohttp.TCPConnector(
            #limit=32,
            family=socket.AF_INET,
            verify_ssl=False,
            )
    with open(LABEL_PATH, "a+b") as fp:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as sess:
            return await tool.limited_api(
                    [record(f"https://danbooru.donmai.us/posts/{i}", sess, fp)
                        for i in range(last_num+1,last_num+max_num+1)])

def read_records():
    with open(LABEL_PATH, "r+b") as fp:
        while fp.read(1):
            fp.seek(-1,1)
            yield pickle.load(fp)

def main():
    #print(len([i for i in read_records()]))
    #exit()
    loop = asyncio.get_event_loop()
    start = 12100
    for i in range(10):
        print(start + i*1000)
        loop.run_until_complete(collect(max_num=1000, last_num=start+i*1000))
        print(start + i*1000)

if __name__ == "__main__":
    main()
