#!/usr/bin/env python3
"""
瓦卡拉NEWs — 新闻爬虫 + 评分脚本
在 GitHub Actions 中定时执行，输出 frontend/news.json
"""

import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from xml.etree import ElementTree

import requests
from bs4 import BeautifulSoup

# ── 配置 ──────────────────────────────────────────────────────
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..",
                            "网站开发", "新闻快讯", "frontend")
NEWS_FILE = os.path.join(FRONTEND_DIR, "news.json")

NEWS_MINIMALIST_URL = "https://www.newsminimalist.com"

GOOGLE_NEWS_FEEDS = {
    "zh": "https://news.google.com/rss?hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    "en": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
}

USER_AGENT = "Mozilla/5.0 (compatible; WakaNews/1.0)"

# 分类关键词
CATEGORY_KEYWORDS = {
    "体育":     ["sports","football","soccer","nba","mlb","f1","tennis","体育","世界杯"],
    "娱乐":     ["entertainment","celebrity","movie","film","hollywood","音乐","电影","明星","娱乐"],
    "科技":     ["tech","technology","ai","artificial intelligence","quantum","software",
                 "semiconductor","芯片","人工智能","科技","算法","大模型"],
    "商业":     ["business","economy","market","gdp","inflation","央行","商业","经济","股市","通胀"],
    "政治":     ["politics","election","government","policy","立法","选举","政府","政策","政治"],
    "国际":     ["world","global","international","国际","全球","世界","联合国"],
    "金融":     ["finance","stocks","bonds","invest","投资","金融","降准"],
}

# 重要性评分关键词
SCORE_KEYWORDS = {
    "global":    ["un","nato","world","global","economy","government","china","united states",
                  "us","europe","eu","央行","经济","政府","中国","美国","欧洲","联合国",
                  "战争","冲突","地震","疫情","发射","载人","深空"],
    "impact":    ["sanction","ban","policy","law","death","market","gdp","interest rate",
                  "通胀","裁员","股市","政策","法律","降准","突破","成功"],
    "novelty":   ["breakthrough","new","first","首次","新","突破","首飞","里程碑"],
    "potential": ["could","may","potential","可能","潜力","ai","quantum","fusion","gen ai",
                  "人工智能","量子","芯片","新能源"],
    "legacy":    ["historic","milestone","anniversary","历史性","里程碑","周年","新时代"],
    "pos":       ["growth","win","improve","increase","agreement","peace",
                  "增长","改善","提高","协议","和平","成功"],
    "neg":       ["crisis","war","conflict","decline","layoff",
                  "死亡","危机","战争","冲突","下滑","裁员"],
}

CREDIBLE_DOMAINS = ["nytimes","bbc","reuters","ft.com","apnews","washingtonpost",
                    "economist","aljazeera","cnbc","bloomberg","wsj","新华","人民"]


# ── 工具函数 ──────────────────────────────────────────────────

def categorize(title: str) -> str:
    t = (title or "").lower()
    for cat, keys in CATEGORY_KEYWORDS.items():
        for k in keys:
            if k in t:
                return cat
    return "综合"


def translate(title: str, src_lang: str = "en") -> str:
    """调用 MyMemory API 翻译为中文（免费，有限速）"""
    if src_lang == "zh":
        return title
    try:
        r = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": title[:500], "langpair": f"{src_lang}|zh-CN"},
            timeout=5,
        )
        data = r.json()
        translated = data.get("responseData", {}).get("translatedText") or title
        return translated
    except Exception:
        return title


def score_news(title: str, source: str = "") -> dict:
    """启发式评分（七因子 → 0-10）"""
    text = f"{title} {source}".lower()
    tl = text

    def hits(keys, base=5.0, step=1.5, cap=10.0):
        s = base + min(sum(1 for k in keys if k in tl), 3) * step
        return min(cap, s)

    scale = hits(SCORE_KEYWORDS["global"])
    impact = hits(SCORE_KEYWORDS["impact"])
    novelty = hits(SCORE_KEYWORDS["novelty"], step=1.2)
    potential = hits(SCORE_KEYWORDS["potential"], step=1.2)
    legacy = hits(SCORE_KEYWORDS["legacy"], base=4.0, step=1.5)

    pos_h = sum(1 for w in SCORE_KEYWORDS["pos"] if w in tl)
    neg_h = sum(1 for w in SCORE_KEYWORDS["neg"] if w in tl)
    positivity = max(0.0, min(10.0, 5.0 + (pos_h - neg_h) * 1.5))

    cred = 5.0
    for d in CREDIBLE_DOMAINS:
        if d in tl:
            cred = 8.0
            break

    w_pos = 0.05
    w_other = 0.95 / 6.0
    computed = (
        w_other * scale + w_other * impact + w_other * novelty
        + w_other * potential + w_other * legacy
        + w_other * cred + w_pos * positivity
    )

    return {
        "score": round(computed, 3),
        "factors": {
            "scale": round(scale, 2),
            "impact": round(impact, 2),
            "novelty": round(novelty, 2),
            "potential": round(potential, 2),
            "legacy": round(legacy, 2),
            "positivity": round(positivity, 2),
            "credibility": round(cred, 2),
        }
    }


def make_item(title: str, url: str, source: str, lang: str,
              pub_time: str = "") -> dict:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cat = categorize(title)
    sc = score_news(title, source)
    return {
        "id": str(uuid.uuid4()),
        "title": title,
        "url": url,
        "source": source,
        "publish_time": pub_time or now,
        "created_at": now,
        "category": cat,
        "language": lang,
        "significance_score": sc["score"],
        "significance_factors": sc["factors"],
    }


# ── 爬虫 ──────────────────────────────────────────────────────

def fetch_google_news(lang: str = "zh", limit: int = 30) -> list:
    """从 Google News RSS 抓取新闻"""
    feed_url = GOOGLE_NEWS_FEEDS.get(lang, GOOGLE_NEWS_FEEDS["en"])
    print(f"  [Google News {lang}] fetching {feed_url}")
    try:
        r = requests.get(feed_url, headers={"User-Agent": USER_AGENT}, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"  [Google News {lang}] FAILED: {e}")
        return []

    items = []
    try:
        root = ElementTree.fromstring(r.content)
        # RSS 路径: rss/channel/item
        for item_elem in root.iter("item"):
            title_el = item_elem.find("title")
            link_el = item_elem.find("link")
            pub_el = item_elem.find("pubDate")

            title = (title_el.text or "").strip() if title_el is not None else ""
            link = (link_el.text or "").strip() if link_el is not None else ""
            pub = (pub_el.text or "").strip() if pub_el is not None else ""

            if not title or not link:
                continue

            # 过滤娱乐/体育
            cat = categorize(title)
            if cat in ("娱乐", "体育"):
                continue

            # 翻译标题
            title_zh = translate(title, lang) if lang != "zh" else title

            items.append(make_item(title_zh, link, "news.google.com", lang, pub))
            if len(items) >= limit:
                break
    except Exception as e:
        print(f"  [Google News {lang}] parse error: {e}")

    print(f"  [Google News {lang}] got {len(items)} items")
    return items


def fetch_newsminimalist(limit: int = 20) -> list:
    """从 News Minimalist 首页提取新闻标题"""
    print(f"  [News Minimalist] fetching {NEWS_MINIMALIST_URL}")
    try:
        r = requests.get(NEWS_MINIMALIST_URL,
                         headers={"User-Agent": USER_AGENT}, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"  [News Minimalist] FAILED: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    items = []

    for a in soup.find_all("a"):
        title = (a.get_text() or "").strip()
        href = a.get("href") or ""
        if not title or not href or href.startswith("#"):
            continue
        if len(title) < 8:
            continue
        if title.lower() in ("home", "about", "contact", "privacy", "terms"):
            continue

        if href.startswith("/"):
            href = NEWS_MINIMALIST_URL.rstrip("/") + href

        title_zh = translate(title, "en")

        items.append(make_item(title_zh, href, "newsminimalist.com", "en"))
        if len(items) >= limit:
            break

    print(f"  [News Minimalist] got {len(items)} items")
    return items


# ── 主流程 ────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print("瓦卡拉NEWs 新闻爬虫 — 开始")
    print(f"时间: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 50)

    all_items = []

    # 1. Google News 中文
    all_items.extend(fetch_google_news("zh", 30))
    # 2. Google News 英文
    all_items.extend(fetch_google_news("en", 20))
    # 3. News Minimalist
    all_items.extend(fetch_newsminimalist(15))

    # 去重（按 URL）
    seen_urls = set()
    unique = []
    for item in all_items:
        if item["url"] not in seen_urls:
            seen_urls.add(item["url"])
            unique.append(item)

    # 按 significance_score 降序
    unique.sort(key=lambda x: x.get("significance_score", 0), reverse=True)

    # 取前 50 条
    final = unique[:50]

    print(f"\n总计: {len(all_items)} → 去重后 {len(unique)} → 取前 {len(final)}")

    # 写入 news.json
    os.makedirs(os.path.dirname(NEWS_FILE), exist_ok=True)
    with open(NEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    print(f"已写入: {NEWS_FILE}")
    print(f"Top 3:")
    for item in final[:3]:
        print(f"  [{item['significance_score']}] {item['title']}")
    print("=" * 50)


if __name__ == "__main__":
    main()
