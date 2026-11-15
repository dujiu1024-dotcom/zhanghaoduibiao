#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTML → 纯文本（标准库实现），用于入库前清洗。"""
import html as htmllib
import re
import sys
from html.parser import HTMLParser


class Extractor(HTMLParser):
    SKIP = {"script", "style", "nav", "header", "footer", "noscript", "svg", "iframe"}
    BLOCK = {"p", "div", "section", "article", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "br", "hr", "blockquote", "td", "th", "figcaption"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skip_depth = 0
        self.in_body = False

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip_depth += 1
        if tag == "body":
            self.in_body = True
        if tag in self.BLOCK:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip_depth > 0:
            self.skip_depth -= 1
        if tag in self.BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if self.skip_depth == 0 and self.in_body:
            self.out.append(data)


def html2text(raw: str) -> str:
    ex = Extractor()
    ex.feed(raw)
    text = "".join(ex.out)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return htmllib.unescape(text).strip()


if __name__ == "__main__":
    raw = open(sys.argv[1], encoding="utf-8", errors="ignore").read()
    txt = html2text(raw)
    open(sys.argv[2], "w", encoding="utf-8").write(txt)
    print(f"{sys.argv[2]}: {len(txt)} 字符")
