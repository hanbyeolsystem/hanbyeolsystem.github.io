"""네이버 블로그 RSS에서 최근 글 6개를 읽어 index.html의 '블로그 소식' 칸을 채운다.

실행: python scripts/update_blog.py
깃허브에서는 .github/workflows/blog.yml 이 하루 3번 실행한다.
"""
import html
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

RSS = "https://rss.blog.naver.com/hanbyeolsystem.xml"
POST_PREFIX = "https://blog.naver.com/hanbyeolsystem/"
COUNT = 6
INDEX = Path(__file__).resolve().parent.parent / "index.html"
MARKERS = re.compile(r"(<!-- BLOG:START[^>]*-->)(.*?)(<!-- BLOG:END -->)", re.S)


def fetch_rss():
    req = urllib.request.Request(RSS, headers={"User-Agent": "Mozilla/5.0 (blog-list-updater)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def parse(xml_bytes):
    posts = []
    for item in ET.fromstring(xml_bytes).iterfind("./channel/item"):
        link = (item.findtext("guid") or "").strip()
        pub = item.findtext("pubDate")
        if not link.startswith(POST_PREFIX) or not pub:  # 우리 블로그 글 주소만 받음
            continue
        img = re.search(r'<img src="(https://[^"]+)"', item.findtext("description") or "")
        posts.append({
            "title": (item.findtext("title") or "").strip(),
            "link": link,
            "date": parsedate_to_datetime(pub),
            "img": img.group(1) if img else None,
        })
        if len(posts) == COUNT:
            break
    return posts


def render(posts):
    e = lambda s: html.escape(s, quote=True)
    rows = []
    for p in posts:
        # 네이버 사진은 다른 사이트 주소를 달고 부르면 막혀서(403) referrer 를 보내지 않음
        img = (f'<img src="{e(p["img"])}" alt="" width="365" height="365" loading="lazy" referrerpolicy="no-referrer">'
               if p["img"] else '<span class="blog-noimg"></span>')
        rows.append(
            f'          <li><a href="{e(p["link"])}" target="_blank" rel="noopener">{img}'
            f'<span class="blog-title">{e(p["title"])}<span class="sr-only"> (새 창)</span></span>'
            f'<time datetime="{p["date"]:%Y-%m-%d}">{p["date"]:%Y.%m.%d}</time></a></li>'
        )
    return '\n        <ul class="blog">\n' + "\n".join(rows) + "\n        </ul>\n        "


def main():
    posts = parse(fetch_rss())
    if not posts:
        sys.exit("RSS에서 글을 하나도 못 읽었습니다. index.html은 그대로 둡니다.")
    with open(INDEX, encoding="utf-8", newline="") as f:
        page = f.read()
    if not MARKERS.search(page):
        sys.exit("index.html에서 BLOG:START / BLOG:END 표시를 못 찾았습니다.")
    new = MARKERS.sub(lambda m: m.group(1) + render(posts) + m.group(3), page, count=1)
    if new == page:
        print("새 글 없음")
        return
    with open(INDEX, "w", encoding="utf-8", newline="") as f:
        f.write(new)
    print(f"블로그 글 {len(posts)}개 반영, 최신: {posts[0]['date']:%Y.%m.%d} {posts[0]['title']}")


if __name__ == "__main__":
    main()
