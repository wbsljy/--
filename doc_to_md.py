#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 Word/Confluence 导出的 .doc（MIME multipart HTML）转换为 Markdown。
保留正文文字与图片的原始顺序，内嵌图片提取到同目录下的 images 文件夹。

用法:
    python doc_to_md.py 2.EasyData任务调度开发案例.doc
    python doc_to_md.py *.doc
    python doc_to_md.py input.doc -o output.md
"""

from __future__ import annotations

import argparse
import base64
import binascii
import mimetypes
import quopri
import re
import sys
import urllib.error
import urllib.request
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup, NavigableString, Tag

SKIP_TAGS = {"style", "script", "meta", "link", "head"}
BLOCK_TAGS = {
    "p", "div", "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li", "table", "pre", "blockquote", "hr",
    "tr", "img", "br",
}
INLINE_BREAK_TAGS = {"br", "img"}


def read_doc_bytes(path: Path) -> bytes:
    return path.read_bytes()


def parse_mime_parts(raw: bytes) -> List[Tuple[Dict[str, str], bytes]]:
    """解析 MIME multipart/related，返回 (headers, body) 列表。"""
    msg = BytesParser(policy=policy.default).parsebytes(raw)
    parts: List[Tuple[Dict[str, str], bytes]] = []

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_maintype() == "multipart":
                continue
            headers = {
                "content-type": part.get_content_type(),
                "content-transfer-encoding": part.get("Content-Transfer-Encoding", ""),
                "content-location": part.get("Content-Location", ""),
            }
            payload = part.get_payload(decode=False)
            if isinstance(payload, str):
                payload = payload.encode("utf-8", errors="replace")
            elif payload is None:
                payload = b""
            parts.append((headers, payload))
        return parts

    # 回退：手动按 boundary 切分
    text = raw.decode("utf-8", errors="replace")
    boundary_match = re.search(r'boundary="?([^"\r\n;]+)"?', text, re.I)
    if not boundary_match:
        raise ValueError("无法识别 MIME boundary，不是支持的 .doc 格式")

    boundary = boundary_match.group(1)
    chunks = re.split(rf"\r?\n--{re.escape(boundary)}(?:--)?\r?\n", text)
    for chunk in chunks[1:]:
        chunk = chunk.strip()
        if not chunk or chunk == "--":
            continue
        header_body = re.split(r"\r?\n\r?\n", chunk, maxsplit=1)
        if len(header_body) != 2:
            continue
        header_text, body_text = header_body
        headers: Dict[str, str] = {}
        for line in header_text.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip().lower()] = value.strip()
        parts.append((headers, body_text.encode("utf-8")))
    return parts


def decode_part_body(headers: Dict[str, str], body: bytes) -> bytes:
    encoding = headers.get("content-transfer-encoding", "").lower()
    if encoding == "base64":
        cleaned = b"".join(body.split())
        pad = (-len(cleaned)) % 4
        if pad:
            cleaned += b"=" * pad
        try:
            return base64.b64decode(cleaned)
        except binascii.Error:
            return body
    if encoding == "quoted-printable":
        return quopri.decodestring(body)
    return body


def location_keys(location: str) -> List[str]:
    """从 Content-Location 生成可用于匹配 img src 的 key 列表。"""
    if not location:
        return []
    loc = unquote(location.strip())
    loc = loc.replace("\\", "/")
    keys = {loc, loc.lower()}
    if "://" in loc:
        path = urlparse(loc).path
        keys.add(path.lstrip("/"))
        keys.add(Path(path).name)
    else:
        keys.add(loc.split("/")[-1])
        keys.add(loc.split(":")[-1].lstrip("/"))
    return [k for k in keys if k]


def guess_extension(content_type: str, data: bytes, fallback_name: str = "") -> str:
    if content_type and content_type != "application/octet-stream":
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if ext:
            return ext
    if fallback_name:
        suffix = Path(fallback_name).suffix
        if suffix:
            return suffix
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if data[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    return ".png"


def build_image_map(parts: List[Tuple[Dict[str, str], bytes]]) -> Dict[str, Tuple[bytes, str]]:
    """content key -> (image_bytes, extension)"""
    image_map: Dict[str, Tuple[bytes, str]] = {}
    for headers, raw_body in parts:
        ctype = headers.get("content-type", "")
        if not ctype.startswith("image/") and ctype not in (
            "application/octet-stream",
            "",
        ):
            # 也接受无 content-type 但 Content-Location 指向图片的 part
            location = headers.get("content-location", "")
            if not re.search(r"\.(png|jpe?g|gif|bmp|webp)$", location, re.I):
                if ctype and not ctype.startswith("text/"):
                    continue
                else:
                    continue
        body = decode_part_body(headers, raw_body)
        if not body or len(body) < 16:
            continue
        location = headers.get("content-location", "")
        ext = guess_extension(ctype, body, location)
        for key in location_keys(location):
            image_map[key] = (body, ext)
        # 纯 hash 名（Confluence 常见）
        base = Path(unquote(location.replace("\\", "/")).split("/")[-1]).stem
        if base:
            image_map[base] = (body, ext)
    return image_map


def extract_html(parts: List[Tuple[Dict[str, str], bytes]]) -> str:
    for headers, raw_body in parts:
        ctype = headers.get("content-type", "")
        if "text/html" in ctype:
            body = decode_part_body(headers, raw_body)
            for encoding in ("utf-8", "gbk", "gb2312", "latin-1"):
                try:
                    return body.decode(encoding)
                except UnicodeDecodeError:
                    continue
            return body.decode("utf-8", errors="replace")
    raise ValueError("未在 .doc 中找到 HTML 正文")


def find_content_root(soup: BeautifulSoup) -> Tag:
    for selector in ("div.Section1", "div.Section0", "div#content", "body"):
        node = soup.select_one(selector)
        if node:
            return node
    return soup.body or soup


def normalize_src(src: str) -> str:
    src = unquote(src.strip().strip('"').strip("'"))
    if not src:
        return src
    if src.startswith("file:"):
        return src.split("/")[-1].split(":")[-1]
    return src


def resolve_image(
    src: str,
    image_map: Dict[str, Tuple[bytes, str]],
    saved_paths: Dict[str, str],
    images_dir: Path,
    image_counter: List[int],
    download_external: bool,
) -> Optional[str]:
    src_norm = normalize_src(src)
    candidates = [src_norm, src_norm.split("/")[-1], Path(src_norm).name]
    if "?" in src_norm:
        candidates.append(src_norm.split("?")[0].split("/")[-1])

    for key in candidates:
        if key in saved_paths:
            return saved_paths[key]
        if key in image_map:
            data, ext = image_map[key]
            image_counter[0] += 1
            filename = f"image-{image_counter[0]}{ext}"
            out_path = images_dir / filename
            out_path.write_bytes(data)
            rel = f"images/{filename}"
            saved_paths[key] = rel
            saved_paths[src_norm] = rel
            return rel

    if src_norm.startswith(("http://", "https://")) and download_external:
        image_counter[0] += 1
        parsed = urlparse(src_norm)
        ext = Path(parsed.path).suffix or ".png"
        filename = f"image-{image_counter[0]}{ext}"
        out_path = images_dir / filename
        try:
            req = urllib.request.Request(
                src_norm,
                headers={"User-Agent": "Mozilla/5.0 doc_to_md/1.0"},
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                out_path.write_bytes(resp.read())
            rel = f"images/{filename}"
            saved_paths[src_norm] = rel
            return rel
        except (urllib.error.URLError, TimeoutError, OSError):
            saved_paths[src_norm] = src_norm
            return src_norm

    if src_norm.startswith(("http://", "https://")):
        return src_norm
    return None


class HtmlToMarkdown:
    def __init__(
        self,
        image_map: Dict[str, Tuple[bytes, str]],
        images_dir: Path,
        download_external: bool = True,
    ):
        self.image_map = image_map
        self.images_dir = images_dir
        self.download_external = download_external
        self.saved_paths: Dict[str, str] = {}
        self.image_counter = [0]
        self.lines: List[str] = []

    def convert(self, html: str) -> str:
        html = re.sub(
            r"<!\[if[^\]]*\]>.*?<!\[endif\]>",
            "",
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )
        html = re.sub(r"<!\[if[^\]]*\]>", "", html, flags=re.IGNORECASE)
        html = re.sub(r"<!\[endif\]>", "", html, flags=re.IGNORECASE)
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all(["o:p"]):
            tag.decompose()
        for tag in soup.find_all(class_=re.compile(r"toc-macro|rbtoc")):
            tag.decompose()
        root = find_content_root(soup)
        self._walk_children(root)
        return self._finalize("\n".join(self.lines))

    def _finalize(self, text: str) -> str:
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip() + "\n"

    def _walk_children(self, node: Tag) -> None:
        for child in node.children:
            self._visit(child)

    def _visit(self, node) -> None:
        if isinstance(node, NavigableString):
            text = self._clean_text(str(node))
            if text:
                self._append_inline(text)
            return

        if not isinstance(node, Tag):
            return

        name = node.name.lower()
        if name in SKIP_TAGS:
            return

        if name in {"strong", "b"}:
            text = node.get_text("", strip=True)
            if text:
                self._append_inline(f"**{text}**")
            return

        if name in {"em", "i"}:
            text = node.get_text("", strip=True)
            if text:
                self._append_inline(f"*{text}*")
            return

        if name == "a":
            text = node.get_text("", strip=True)
            href = node.get("href", "").strip()
            if text and href and not href.startswith("#"):
                self._append_inline(f"[{text}]({href})")
            elif text:
                self._append_inline(text)
            return

        if name == "img":
            rendered = self._render_image(node).strip()
            if rendered:
                self._append_block(rendered)
            return

        if name == "br":
            self._append_inline("\n")
            return

        if name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            level = int(name[1])
            text = node.get_text(" ", strip=True)
            if text:
                self._append_block(f"{'#' * level} {text}")
            return

        if name == "li":
            text = self._inline_text(node)
            if text:
                self._append_block(f"- {text}")
            return

        if name in {"ul", "ol"}:
            for li in node.find_all("li", recursive=False):
                self._visit(li)
            return

        if name == "table":
            self._append_table(node)
            return

        if name == "pre":
            code = node.get_text("\n", strip=False).strip("\n")
            if code:
                self._append_block(f"```\n{code}\n```")
            return

        if name == "div":
            classes = " ".join(node.get("class", []))
            if "table-wrap" in classes or (node.find("table") and not node.find("p")):
                table = node.find("table")
                if table:
                    self._append_table(table)
                    return
            if self._should_skip_container(node):
                return
            self._walk_children(node)
            return

        if name == "p":
            if self._should_skip_container(node):
                return
            block = self._inline_from_children(node)
            if block.strip() and not self._is_toc_only_paragraph(node, block):
                self._append_block(block)
            return

        if name == "tr":
            return

        # 其他容器：递归子节点
        self._walk_children(node)

    def _should_skip_container(self, node: Tag) -> bool:
        classes = " ".join(node.get("class", []))
        return "toc-macro" in classes or "rbtoc" in classes

    def _is_toc_only_paragraph(self, node: Tag, block: str) -> bool:
        """跳过 Word 导出里仅含目录锚点的段落。"""
        anchors = node.find_all("a")
        if not anchors:
            return False
        anchor_text = "".join(a.get_text(strip=True) for a in anchors)
        return anchor_text and anchor_text == block.replace("·", "").replace("•", "").strip()

    def _render_image(self, img: Tag) -> str:
        src = img.get("src", "")
        alt = img.get("alt", "") or "image"
        path = resolve_image(
            src,
            self.image_map,
            self.saved_paths,
            self.images_dir,
            self.image_counter,
            self.download_external,
        )
        if path:
            return f"\n\n![{alt}]({path})\n\n"
        return ""

    def _inline_from_children(self, node: Tag) -> str:
        parts: List[str] = []
        for child in node.children:
            if isinstance(child, NavigableString):
                text = self._clean_text(str(child))
                if text:
                    parts.append(text)
            elif isinstance(child, Tag):
                cname = child.name.lower()
                if cname in SKIP_TAGS:
                    continue
                if cname == "img":
                    parts.append(self._render_image(child))
                elif cname == "br":
                    parts.append("\n")
                elif cname in {"strong", "b"}:
                    inner = self._inline_from_children(child)
                    if inner:
                        parts.append(f"**{inner}**")
                elif cname in {"em", "i"}:
                    inner = self._inline_from_children(child)
                    if inner:
                        parts.append(f"*{inner}*")
                elif cname == "a":
                    t = self._inline_from_children(child) or child.get_text("", strip=True)
                    href = child.get("href", "").strip()
                    if t and href and not href.startswith("#"):
                        parts.append(f"[{t}]({href})")
                    elif t:
                        parts.append(t)
                else:
                    parts.append(self._inline_from_children(child))
        return "".join(parts).strip()

    def _inline_text(self, node: Tag) -> str:
        return self._inline_from_children(node) if node.name == "li" else node.get_text(" ", strip=True)

    def _append_table(self, table: Tag) -> None:
        rows: List[List[str]] = []
        for tr in table.find_all("tr"):
            cells = [
                self._clean_text(td.get_text(" ", strip=True))
                for td in tr.find_all(["th", "td"])
            ]
            if any(cells):
                rows.append(cells)
        if not rows:
            return
        col_count = max(len(r) for r in rows)
        rows = [r + [""] * (col_count - len(r)) for r in rows]
        lines = [
            "| " + " | ".join(rows[0]) + " |",
            "| " + " | ".join(["---"] * col_count) + " |",
        ]
        for row in rows[1:]:
            lines.append("| " + " | ".join(row) + " |")
        self._append_block("\n".join(lines))

    def _append_block(self, text: str) -> None:
        text = text.strip()
        if not text:
            return
        if self.lines and not self.lines[-1].endswith("\n"):
            self.lines.append("")
        self.lines.append(text)
        self.lines.append("")

    def _append_inline(self, text: str) -> None:
        if not self.lines:
            self.lines.append(text)
        else:
            self.lines[-1] += text

    @staticmethod
    def _clean_text(text: str) -> str:
        text = text.replace("\xa0", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()


def convert_doc_to_md(
    doc_path: Path,
    output_path: Optional[Path] = None,
    download_external: bool = True,
) -> Path:
    doc_path = doc_path.resolve()
    if output_path is None:
        output_path = doc_path.with_suffix(".md")
    else:
        output_path = output_path.resolve()

    images_dir = output_path.parent / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    raw = read_doc_bytes(doc_path)
    parts = parse_mime_parts(raw)
    html = extract_html(parts)
    image_map = build_image_map(parts)

    converter = HtmlToMarkdown(image_map, images_dir, download_external)
    markdown = converter.convert(html)
    output_path.write_text(markdown, encoding="utf-8")

    print(
        f"已转换: {doc_path.name} -> {output_path.name} "
        f"({converter.image_counter[0]} 张图片)"
    )
    return output_path


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="将 .doc (MIME HTML) 转换为 Markdown")
    parser.add_argument("inputs", nargs="+", help="输入 .doc 文件路径")
    parser.add_argument("-o", "--output", help="输出 .md 路径（仅单文件时有效）")
    parser.add_argument(
        "--no-download-external",
        action="store_true",
        help="不下载外链图片，保留原始 URL",
    )
    args = parser.parse_args(argv)

    output_path = Path(args.output) if args.output else None
    if output_path and len(args.inputs) > 1:
        print("错误: -o 仅支持单个输入文件", file=sys.stderr)
        return 1

    for item in args.inputs:
        path = Path(item)
        if not path.exists():
            print(f"跳过（不存在）: {path}", file=sys.stderr)
            continue
        try:
            convert_doc_to_md(
                path,
                output_path,
                download_external=not args.no_download_external,
            )
        except Exception as exc:
            print(f"转换失败 {path}: {exc}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
