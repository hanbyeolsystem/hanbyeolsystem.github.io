"""실행: python -m unittest discover -s scripts"""
import unittest

from update_blog import MARKERS, parse, render

SAMPLE = """<?xml version="1.0" encoding="UTF-8"?><rss><channel>
<item><title><![CDATA[<b>"NAS" & 백업</b>]]></title><guid>https://blog.naver.com/hanbyeolsystem/1</guid>
<description><![CDATA[본문 <img src="https://blogthumb.pstatic.net/a.png?type=s3&x=1" />]]></description>
<pubDate>Thu, 19 Nov 2026 18:30:09 +0900</pubDate></item>
<item><title>남의 글</title><guid>https://evil.example/2</guid><pubDate>Thu, 19 Nov 2026 18:30:09 +0900</pubDate></item>
<item><title>사진 없는 글</title><guid>https://blog.naver.com/hanbyeolsystem/3</guid>
<description>본문</description><pubDate>Wed, 18 Nov 2026 09:00:00 +0900</pubDate></item>
</channel></rss>""".encode("utf-8")


class UpdateBlogTest(unittest.TestCase):
    def test_parse_and_render(self):
        posts = parse(SAMPLE)
        self.assertEqual([p["link"][-1] for p in posts], ["1", "3"])  # 다른 주소 글은 버림
        out = render(posts)
        self.assertEqual(out.count("<li>"), 2)
        self.assertIn("&lt;b&gt;&quot;NAS&quot; &amp; 백업&lt;/b&gt;", out)  # 제목 속 태그는 글자로만
        self.assertIn("a.png?type=s3&amp;x=1", out)
        self.assertIn('datetime="2026-11-19">2026.11.19<', out)
        self.assertIn('class="blog-noimg"', out)
        self.assertIn('target="_blank" rel="noopener"', out)

    def test_markers_replace_only_inside(self):
        page = "앞<!-- BLOG:START 설명 -->옛것<!-- BLOG:END -->뒤"
        new = MARKERS.sub(lambda m: m.group(1) + "새것" + m.group(3), page, count=1)
        self.assertEqual(new, "앞<!-- BLOG:START 설명 -->새것<!-- BLOG:END -->뒤")


if __name__ == "__main__":
    unittest.main()
