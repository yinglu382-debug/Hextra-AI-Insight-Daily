import asyncio
import re
from typing import Dict, List

import httpx
from bs4 import BeautifulSoup


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


HEADERS = {"User-Agent": USER_AGENT, "Accept-Language": "zh-CN,zh;q=0.9"}


def first_paragraph_or_video_html(soup: BeautifulSoup) -> str:
    # Try to find a first paragraph of meaningful text
    for p in soup.select("p"):
        text = p.get_text(strip=True)
        if text and len(text) >= 20:
            return f"<p>{text}</p>"

    # Try to find embedded video
    iframe = soup.find("iframe")
    if iframe and iframe.get("src"):
        src = iframe["src"]
        return f"<iframe src=\"{src}\" allow=\"autoplay; encrypted-media\" allowfullscreen loading=\"lazy\"></iframe>"

    video = soup.find("video")
    if video and video.get("src"):
        src = video["src"]
        return f"<video src=\"{src}\" controls></video>"

    return ""


async def fetch_html(client: httpx.AsyncClient, url: str) -> str:
    resp = await client.get(url, timeout=20.0)
    resp.raise_for_status()
    return resp.text


async def scrape_list_items(client: httpx.AsyncClient, url: str, selectors: List[str]) -> List[Dict]:
    try:
        html = await fetch_html(client, url)
    except Exception:
        return []
    soup = BeautifulSoup(html, "html.parser")
    items: List[Dict] = []
    for selector in selectors:
        for a in soup.select(selector):
            title = a.get_text(strip=True)
            href = a.get("href") or ""
            if not title or not href:
                continue
            if href.startswith("//"):
                href = "https:" + href
            if href.startswith("/"):
                # Best-effort resolve with base URL
                m = re.match(r"^(https?://[^/]+)", url)
                if m:
                    href = m.group(1) + href
            items.append({"title": title, "url": href})
    # de-duplicate by url
    unique: Dict[str, Dict] = {}
    for it in items:
        unique[it["url"]] = it
    return list(unique.values())[:20]


async def enrich_with_summary(client: httpx.AsyncClient, item: Dict) -> Dict:
    url = item["url"]
    try:
        html = await fetch_html(client, url)
    except Exception:
        return {"title": item["title"], "url": url, "summary_html": "", "source": source_from_url(url)}
    soup = BeautifulSoup(html, "html.parser")
    summary_html = first_paragraph_or_video_html(soup)
    return {
        "title": item["title"],
        "url": url,
        "summary_html": summary_html,
        "source": source_from_url(url),
    }


def source_from_url(url: str) -> str:
    if "ithome.com" in url:
        return "IT之家"
    if "sina.com.cn" in url or "smartcn.cn" in url:
        return "新浪科技"
    if "36kr.com" in url:
        return "36氪"
    if "news.cn" in url:
        return "新华网"
    return "来源网站"


async def scrape_category(client: httpx.AsyncClient, category: str) -> List[Dict]:
    tasks: List[asyncio.Task] = []

    def add(url: str, selectors: List[str]):
        tasks.append(asyncio.create_task(scrape_list_items(client, url, selectors)))

    if category == "手机":
        add("https://mobile.ithome.com/", ["a[href][title]", "h2 a", "h3 a"])
        add("https://mobile.sina.com.cn/", ["a[href][title]", "h2 a", "h3 a"])
        add("https://www.36kr.com/search/articles/%E6%89%8B%E6%9C%BA", ["a.article-item-title", "a[href*='/p/']"]) 
    elif category == "智能家电":
        add("https://www.smartcn.cn/news", [".news_list a", "h2 a", "h3 a"]) 
        add("https://www.36kr.com/search/articles/%E6%99%BA%E8%83%BD%E5%AE%B6%E7%94%B5", ["a.article-item-title", "a[href*='/p/']"]) 
    elif category == "汽车":
        add("https://www.news.cn/auto/index.html", ["a[href][title]", "h2 a", "h3 a"]) 
        add("https://www.36kr.com/information/travel/", ["a.article-item-title", "a[href*='/p/']"]) 
    elif category == "芯片":
        add("https://so.news.cn/#search/0/%E8%8A%AF%E7%89%87/1/0", ["a[href][title]", "h2 a", "h3 a"]) 
        add("https://www.ithome.com/search/%E8%8A%AF%E7%89%87.html", ["a[href][title]", "h2 a", "h3 a"]) 
        add("https://www.36kr.com/search/articles/%E8%8A%AF%E7%89%87", ["a.article-item-title", "a[href*='/p/']"]) 
    elif category == "操作系统":
        add("https://search.sina.com.cn/?ac=product&from=tech_index&source=tech&range=title&f_name=&col=&c=news&ie=utf-8&c=news&q=%E6%93%8D%E4%BD%9C%E7%B3%BB%E7%BB%9F", ["a[href][title]", "h2 a", "h3 a"]) 
        add("https://www.36kr.com/search/articles/%E6%93%8D%E4%BD%9C%E7%B3%BB%E7%BB%9F", ["a.article-item-title", "a[href*='/p/']"]) 
    else:
        return []

    lists = await asyncio.gather(*tasks, return_exceptions=True)
    flattened: List[Dict] = []
    for res in lists:
        if isinstance(res, list):
            flattened.extend(res)
    # unique by url
    dedup: Dict[str, Dict] = {}
    for it in flattened:
        dedup[it["url"]] = it
    # Enrich few items per category
    selected = list(dedup.values())[:12]
    enriched = await asyncio.gather(*(enrich_with_summary(client, it) for it in selected))
    return [e for e in enriched if e]


async def fetch_all_categories() -> Dict[str, List[Dict]]:
    categories = ["手机", "智能家电", "汽车", "操作系统", "芯片"]
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        results = await asyncio.gather(*(scrape_category(client, c) for c in categories))
    return {c: r for c, r in zip(categories, results)}

