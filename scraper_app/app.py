import asyncio
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .scraper import fetch_all_categories


class NewsItem(BaseModel):
    title: str
    url: str
    summary_html: str
    source: str
    published_at: Optional[str] = None


class PageState(BaseModel):
    last_updated_iso: str
    data: Dict[str, List[NewsItem]]


app = FastAPI(title="宏观经济研究 - 聚合资讯")

state: PageState = PageState(last_updated_iso="", data={})


def get_category_icon(category: str) -> str:
    mapping = {
        "手机": "📱",
        "智能家电": "🏠",
        "汽车": "🚗",
        "操作系统": "💻",
        "芯片": "💾",
    }
    return mapping.get(category, "📰")


async def refresh_data() -> None:
    global state
    data = await fetch_all_categories()
    state = PageState(
        last_updated_iso=datetime.utcnow().isoformat() + "Z",
        data={k: [NewsItem(**item) for item in v] for k, v in data.items()},
    )


@app.on_event("startup")
async def on_startup():
    # Initial load
    await refresh_data()
    # Hourly refresh
    scheduler = AsyncIOScheduler()
    scheduler.add_job(refresh_data, "interval", hours=1, id="hourly_refresh", max_instances=1, coalesce=True)
    scheduler.start()


@app.get("/data.json")
async def get_data():
    return JSONResponse(state.dict())


@app.get("/")
async def index() -> HTMLResponse:
    last_updated_local = state.last_updated_iso
    sections_html: List[str] = []
    for category, items in state.data.items():
        icon = get_category_icon(category)
        section_items = []
        for item in items:
            section_items.append(
                f"""
                <article class=\"news-item\">
                  <h3 class=\"news-title\"><a href=\"{item.url}\" target=\"_blank\" rel=\"noopener noreferrer\">{item.title}</a></h3>
                  <div class=\"news-summary\">{item.summary_html}</div>
                  <div class=\"news-meta\">
                    <span class=\"source\">来源：{item.source}</span>
                    <a class=\"origin\" href=\"{item.url}\" target=\"_blank\" rel=\"noopener noreferrer\">原文链接 ↗</a>
                  </div>
                </article>
                """
            )
        sections_html.append(
            f"""
            <section>
              <h2>一、{category} <span class=\"icon\">{icon}</span></h2>
              {''.join(section_items) if section_items else '<p class=\"empty\">暂无数据</p>'}
            </section>
            """
        )

    html = f"""
    <!doctype html>
    <html lang=\"zh-CN\">
    <head>
      <meta charset=\"utf-8\" />
      <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
      <title>宏观经济研究 - 聚合资讯</title>
      <style>
        :root {{
          --bg: #0b0f17;
          --card: #121826;
          --text: #e6eefc;
          --muted: #8aa0c6;
          --accent: #3b82f6;
          --border: #22304a;
        }}
        * {{ box-sizing: border-box; }}
        body {{
          margin: 0; padding: 24px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
          color: var(--text); background: linear-gradient(180deg, #0b0f17 0%, #0e1525 100%);
        }}
        header {{ max-width: 1080px; margin: 0 auto 16px auto; padding: 8px 8px 24px; }}
        h1 {{ font-size: 28px; margin: 0 0 8px 0; letter-spacing: 0.5px; }}
        .meta {{ color: var(--muted); font-size: 13px; }}
        main {{ max-width: 1080px; margin: 0 auto; display: grid; gap: 18px; }}
        section {{ background: rgba(18,24,38,0.8); border: 1px solid var(--border); border-radius: 14px; padding: 14px; backdrop-filter: blur(8px); }}
        section h2 {{ font-size: 20px; margin: 4px 6px 12px; display: flex; align-items: center; gap: 8px; }}
        .icon {{ font-size: 20px; }}
        .news-item {{ border-top: 1px dashed var(--border); padding: 12px 6px; }}
        .news-item:first-of-type {{ border-top: none; }}
        .news-title {{ margin: 0 0 8px; font-size: 16px; }}
        .news-title a {{ color: var(--text); text-decoration: none; border-bottom: 1px dashed transparent; }}
        .news-title a:hover {{ color: var(--accent); border-bottom-color: var(--accent); }}
        .news-summary {{ color: #d6e1f5; line-height: 1.6; font-size: 15px; }}
        .news-summary p {{ margin: 6px 0; }}
        .news-summary iframe, .news-summary video {{ width: 100%; max-height: 380px; border: none; border-radius: 10px; background: #000; }}
        .news-meta {{ margin-top: 8px; color: var(--muted); font-size: 13px; display: flex; gap: 12px; align-items: center; }}
        .news-meta a.origin {{ color: var(--muted); text-decoration: none; }}
        .news-meta a.origin:hover {{ color: var(--accent); }}
        .empty {{ color: var(--muted); padding: 8px; }}
        footer {{ max-width: 1080px; margin: 8px auto 0; color: var(--muted); font-size: 12px; text-align: center; }}
      </style>
    </head>
    <body>
      <header>
        <h1>宏观经济研究</h1>
        <div class=\"meta\">每小时自动更新 · 上次更新：{last_updated_local}</div>
      </header>
      <main>
        {''.join(sections_html)}
      </main>
      <footer>仅供学习与参考，内容均来自各来源网站，版权归原网站所有。</footer>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("scraper_app.app:app", host="0.0.0.0", port=8000, reload=False)

