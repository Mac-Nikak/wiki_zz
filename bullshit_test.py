import aiohttp
import asyncio
import re

main_page = {'https://ru.wikipedia.org/wiki/%D0%97%D0%B0%D0%B3%D0%BB%D0%B0%D0%B2%D0%BD%D0%B0%D1%8F_%D1%81%D1%82%D1%80'
             '%D0%B0%D0%BD%D0%B8%D1%86%D0%B0', 'https://ru.wikipedia.org/wiki/'}
file = open('html.txt', 'w')
storage = set()
network = 0
non_network = 0


async def get_html(url: str, session: aiohttp.ClientSession) -> str:
        async with session.get(url) as response:
            return await response.text()


async def find_links(raw_html: str) -> list:
    re_comp = re.compile(r'href="(.*?)"')
    raw_links = re_comp.findall(raw_html)
    links = ('https://ru.wikipedia.org' + link for link in raw_links
             if link[0:5] == '/wiki' and link.find(':') == -1
             and 'https://ru.wikipedia.org' + link not in main_page
             and 'https://ru.wikipedia.org' + link not in storage)
    return list(links)


async def check_if_in2(goal_html: str, link_html: str, goal: str, q: asyncio.Queue,
                      source: str, ancestors: list, links:list):
    if goal_html.find(link_html) == 0:
        return True
    else:
        new_ancestors = ancestors.copy()
        new_ancestors.append(source)
        for link in links:
            await q.put((link, new_ancestors))
            storage.add(link)
        return False



async def check_if_in3(goal_title: str, link_html: str, goal: str, q: asyncio.Queue,
                      source: str, ancestors: list, links:list):
    link_title = get_title(link_html)
    if link_title == goal_title:
        return True
    else:
        new_ancestors = ancestors.copy()
        new_ancestors.append(source)
        for link in links:
            await q.put((link, new_ancestors))
            storage.add(link)
        return False

def get_title(html: str):
    start = html.find('<title>') + 7
    end = html.find('</title>')
    return html[start:end]


async def process_one_url(source: str, ancestors: list, session: aiohttp.ClientSession,
                          goal: str, queue: asyncio.Queue,
                          goal_title: str) -> None:
    raw_html = await get_html(source, session)
    links = await find_links(raw_html)
    check = await check_if_in3(goal_title, raw_html, goal, queue, source, ancestors, links)
    #check = await check_if_in(links,goal,queue,source,ancestors)
    if check:
        ancestors.append(source)
        print(*ancestors)
        for task in (task for task in asyncio.all_tasks() if not task.done()):
            task.cancel()



async def main(source: str, goal: str):
    q = asyncio.Queue()
    storage.add(source)
    session = aiohttp.ClientSession()
    await q.put((source, []))
    goal_title = get_title(await get_html(goal, session))
    i = 0
    j = 0
    while True:
        try:
            z = min(256, q.qsize())
            coros1 = (q.get() for i in range(z))
            links = await asyncio.gather(*coros1)
            coros = (process_one_url(
                x[0], x[1], session, goal, q, goal_title) for x in links
            )
            await asyncio.gather(*coros)
            i += 1
            if i == 2:
                await session.close()
                session = aiohttp.ClientSession()
            print(i)
            j += z
            if i % 10 == 0:
                print(f'We have checked {j} links, nothing found {i}.')
        except asyncio.exceptions.CancelledError as e:
            print('Result found!')
            break

source = 'https://ru.wikipedia.org/wiki/%D0%9F%D1%80%D0%BE%D1%81%D1%82%D1%80%D0%B0%D0%BD%D1%81%D1%82%D0%B2%D0%BE_(%D0%BC%D0%B0%D1%82%D0%B5%D0%BC%D0%B0%D1%82%D0%B8%D0%BA%D0%B0)'
goal = 'https://ru.wikipedia.org/wiki/%D0%9F%D1%80%D0%BE%D1%81%D1%82%D1%80%D0%B0%D0%BD%D1%81%D1%82%D0%B2%D0%BE_%D0%B2_%D1%84%D0%B8%D0%B7%D0%B8%D0%BA%D0%B5'

asyncio.run(main(source, goal))
