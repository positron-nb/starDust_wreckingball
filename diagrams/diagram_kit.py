"""Minimal explicit-layout block-diagram kit: one Python description -> SVG (editable vector),
Mermaid (.mmd logical export of the same nodes/edges) and PNG (rendered by headless Edge/Chrome)."""
from __future__ import annotations

import html
import pathlib
import subprocess
import tempfile

from PIL import Image, ImageChops

STYLES = {
    # name: (stroke, width, dash, arrow)
    "info": ("#3d4654", 2.2, None, True),
    "info2": ("#3d4654", 1.6, "7 5", True),
    "power": ("#c98a00", 5.0, None, True),
    "logic": ("#1f8a4c", 2.6, None, True),
    "safety": ("#c62828", 3.6, None, True),
    "status": ("#c62828", 2.0, "8 6", True),
    "dev": ("#8c8c8c", 2.0, "4 5", False),
    "charge": ("#8c8c8c", 2.2, "6 5", True),
}
KINDS = {
    # name: (fill, stroke, title colour)
    "sense": ("#efe7fb", "#7b4bc4", "#2b1856"),
    "comp": ("#e3f4ea", "#1f8a4c", "#0f3a22"),
    "mcu": ("#e1f0f6", "#1d7894", "#0b3240"),
    "act": ("#e6eefb", "#2b5cb8", "#0e2350"),
    "pwr": ("#fff4d6", "#c98a00", "#4a3300"),
    "safe": ("#fde8e8", "#c62828", "#5a0c0c"),
    "dev": ("#f4f4f4", "#9a9a9a", "#555555"),
    "note": ("#fffbe6", "#d8c26a", "#4a4020"),
    "state": ("#ffffff", "#3d4654", "#1b2230"),
    "state_hot": ("#fde8e8", "#c62828", "#5a0c0c"),
}
FONT = "Arial, Helvetica, sans-serif"


class Box:
    def __init__(self, bid, x0, y0, x1, y1, title, lines=(), kind="comp", rx=10):
        self.id, self.x0, self.y0, self.x1, self.y1 = bid, x0, y0, x1, y1
        self.title, self.lines, self.kind, self.rx = title, list(lines), kind, rx

    def anchor(self, side, frac=0.5):
        if side == "l":
            return (self.x0, self.y0 + frac * (self.y1 - self.y0))
        if side == "r":
            return (self.x1, self.y0 + frac * (self.y1 - self.y0))
        if side == "t":
            return (self.x0 + frac * (self.x1 - self.x0), self.y0)
        if side == "b":
            return (self.x0 + frac * (self.x1 - self.x0), self.y1)
        raise ValueError(side)


class Diagram:
    def __init__(self, name, w, h, title, sub=""):
        self.name, self.w, self.h, self.title, self.sub = name, w, h, title, sub
        self.boxes, self.edges, self.groups, self.texts, self.legend = {}, [], [], [], []

    # ------------------------------------------------------------------ building
    def box(self, bid, x0, y0, x1, y1, title, lines=(), kind="comp", rx=10):
        self.boxes[bid] = Box(bid, x0, y0, x1, y1, title, lines, kind, rx)
        return self.boxes[bid]

    def group(self, x0, y0, x1, y1, title, color="#9aa3b2", fill="#f7f8fa", dash=None):
        self.groups.append((x0, y0, x1, y1, title, color, fill, dash))

    def edge(self, src, dst, style="info", label=None, s="r", d="l", sf=0.5, df=0.5, via=(), lab=None,
             lab_anchor="middle", bi=False):
        """src/dst: box id, or an (x, y) point (e.g. a group frame edge)."""
        self.edges.append(dict(src=src, dst=dst, style=style, label=label, s=s, d=d, sf=sf, df=df,
                               via=list(via), lab=lab, lab_anchor=lab_anchor, bi=bi))

    def _end(self, ref, side, frac):
        return tuple(ref) if isinstance(ref, tuple) else self.boxes[ref].anchor(side, frac)

    def text(self, x, y, s, size=15, color="#555d6b", weight="normal", anchor="start"):
        self.texts.append((x, y, s, size, color, weight, anchor))

    # ------------------------------------------------------------------ geometry
    def _points(self, e):
        a = self._end(e["src"], e["s"], e["sf"])
        b = self._end(e["dst"], e["d"], e["df"])
        pts = [a] + [tuple(p) for p in e["via"]] + [b]
        if not e["via"]:
            if e["s"] in "lr" and e["d"] in "lr" and abs(a[1] - b[1]) > 0.5:
                xm = (a[0] + b[0]) / 2
                pts = [a, (xm, a[1]), (xm, b[1]), b]
            elif e["s"] in "tb" and e["d"] in "tb" and abs(a[0] - b[0]) > 0.5:
                ym = (a[1] + b[1]) / 2
                pts = [a, (a[0], ym), (b[0], ym), b]
            elif e["s"] in "lr" and e["d"] in "tb":
                pts = [a, (b[0], a[1]), b]
            elif e["s"] in "tb" and e["d"] in "lr":
                pts = [a, (a[0], b[1]), b]
        return pts

    # ------------------------------------------------------------------ SVG
    def svg(self):
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
               f'viewBox="0 0 {self.w} {self.h}" font-family="{FONT}">',
               "<defs>"]
        for nm, (col, wd, dash, arrow) in STYLES.items():
            out.append(f'<marker id="ah_{nm}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="{4.2 if wd > 3 else 6}" '
                       f'markerHeight="{4.2 if wd > 3 else 6}" orient="auto-start-reverse">'
                       f'<path d="M0,0 L10,5 L0,10 z" fill="{col}"/></marker>')
        out.append("</defs>")
        out.append(f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="#ffffff"/>')
        out.append(f'<text x="24" y="44" font-size="30" font-weight="bold" fill="#1b2230">{html.escape(self.title)}</text>')
        if self.sub:
            for k, line in enumerate(self.sub.split("\n")):
                out.append(f'<text x="24" y="{76 + 22 * k}" font-size="17" fill="#555d6b">{html.escape(line)}</text>')
        for x0, y0, x1, y1, title, color, fill, dash in self.groups:
            ds = f' stroke-dasharray="{dash}"' if dash else ""
            out.append(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="14" fill="{fill}" '
                       f'stroke="{color}" stroke-width="2"{ds}/>')
            out.append(f'<text x="{x0 + 14}" y="{y0 + 24}" font-size="16" font-weight="bold" fill="{color}">'
                       f'{html.escape(title)}</text>')
        for e in self.edges:
            col, wd, dash, arrow = STYLES[e["style"]]
            pts = self._points(e)
            d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
            ds = f' stroke-dasharray="{dash}"' if dash else ""
            mk = f' marker-end="url(#ah_{e["style"]})"' if arrow else ""
            if arrow and e.get("bi"):
                mk += f' marker-start="url(#ah_{e["style"]})"'
            out.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{wd}" '
                       f'stroke-linejoin="round"{ds}{mk}/>')
        for b in self.boxes.values():
            fill, stroke, tc = KINDS[b.kind]
            sw = 2.6 if b.kind in ("safe", "state_hot") else 2.0
            ds = ' stroke-dasharray="6 5"' if b.kind == "dev" else ""
            out.append(f'<rect x="{b.x0}" y="{b.y0}" width="{b.x1 - b.x0}" height="{b.y1 - b.y0}" rx="{b.rx}" '
                       f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{ds}/>')
            n = 1 + len(b.lines)
            lh_t, lh = 21, 19
            total = lh_t + lh * (n - 1)
            y = (b.y0 + b.y1) / 2 - total / 2 + 15
            cx = (b.x0 + b.x1) / 2
            out.append(f'<text x="{cx}" y="{y:.1f}" font-size="17" font-weight="bold" fill="{tc}" '
                       f'text-anchor="middle">{html.escape(b.title)}</text>')
            y += lh_t
            for line in b.lines:
                out.append(f'<text x="{cx}" y="{y:.1f}" font-size="15" fill="#263040" text-anchor="middle">'
                           f'{html.escape(line)}</text>')
                y += lh
        for e in self.edges:
            if not e["label"]:
                continue
            col = STYLES[e["style"]][0]
            if e["lab"] is not None:
                lx, ly = e["lab"]
            else:
                pts = self._points(e)
                seg = max(range(len(pts) - 1), key=lambda i: abs(pts[i + 1][0] - pts[i][0]) + abs(pts[i + 1][1] - pts[i][1]))
                lx = (pts[seg][0] + pts[seg + 1][0]) / 2
                ly = (pts[seg][1] + pts[seg + 1][1]) / 2
            lines = e["label"].split("\n")
            wmax = max(len(t) for t in lines) * 7.6 + 12
            hh = 19 * len(lines) + 6
            x0 = lx - wmax / 2 if e["lab_anchor"] == "middle" else (lx if e["lab_anchor"] == "start" else lx - wmax)
            out.append(f'<rect x="{x0:.1f}" y="{ly - hh / 2:.1f}" width="{wmax:.1f}" height="{hh:.1f}" rx="5" '
                       f'fill="#ffffff" fill-opacity="0.94" stroke="none"/>')
            for k, t in enumerate(lines):
                yy = ly - hh / 2 + 18 + 19 * k
                out.append(f'<text x="{x0 + wmax / 2:.1f}" y="{yy:.1f}" font-size="14.5" fill="{col}" '
                           f'text-anchor="middle" font-style="italic">{html.escape(t)}</text>')
        for x, y, s, size, color, weight, anchor in self.texts:
            for k, line in enumerate(s.split("\n")):
                out.append(f'<text x="{x}" y="{y + k * (size + 4)}" font-size="{size}" fill="{color}" '
                           f'font-weight="{weight}" text-anchor="{anchor}">{html.escape(line)}</text>')
        if self.legend:
            lx, ly = self.legend_xy
            for k, (style, txt) in enumerate(self.legend):
                col, wd, dash, arrow = STYLES[style]
                ds = f' stroke-dasharray="{dash}"' if dash else ""
                xx = lx + k * self.legend_dx
                out.append(f'<line x1="{xx}" y1="{ly}" x2="{xx + 46}" y2="{ly}" stroke="{col}" stroke-width="{wd}"{ds}/>')
                out.append(f'<text x="{xx + 56}" y="{ly + 5}" font-size="15" fill="#333">{html.escape(txt)}</text>')
        out.append("</svg>")
        return "\n".join(out)

    def set_legend(self, items, x, y, dx=300):
        self.legend, self.legend_xy, self.legend_dx = items, (x, y), dx

    # ------------------------------------------------------------------ Mermaid export
    def mermaid(self):
        cls = {}
        lines = [f"%% {self.title}", "%% Logical export generated by build_diagrams.py from the same node/edge data as",
                 "%% the presentation SVG/PNG.  Edit build_diagrams.py, not this file.", "flowchart LR"]
        for b in self.boxes.values():
            label = "<b>" + b.title + "</b>" + "".join("<br/>" + t for t in b.lines)
            label = label.replace('"', "'")
            lines.append(f'  {b.id}["{label}"]')
            cls.setdefault(b.kind, []).append(b.id)
        arrows = {"info": "-->", "info2": "-.->", "power": "==>", "logic": "-->", "safety": "==>",
                  "status": "-.->", "dev": "-.-", "charge": "-.->"}
        kept = [e for e in self.edges if isinstance(e["src"], str) and isinstance(e["dst"], str)]
        for e in kept:
            lab = f'|"{e["label"].replace(chr(10), " ")}"|' if e["label"] else ""
            arr = "<-->" if e.get("bi") else arrows[e["style"]]
            lines.append(f'  {e["src"]} {arr}{lab} {e["dst"]}')
        for k, (fill, stroke, tc) in KINDS.items():
            lines.append(f"  classDef {k} fill:{fill},stroke:{stroke},color:{tc}")
        for k, ids in cls.items():
            lines.append(f"  class {','.join(ids)} {k}")
        for i, e in enumerate(kept):
            col, wd, dash, _ = STYLES[e["style"]]
            dd = f",stroke-dasharray:{dash.replace(' ', ' ')}" if dash else ""
            lines.append(f"  linkStyle {i} stroke:{col},stroke-width:{wd}px{dd}")
        return "\n".join(lines) + "\n"

    # ------------------------------------------------------------------ outputs
    def write(self, svg_dir: pathlib.Path, mmd_dir: pathlib.Path, png_dir: pathlib.Path, browser: str):
        svg_dir.mkdir(parents=True, exist_ok=True)
        svg_path = svg_dir / f"{self.name}.svg"
        svg_path.write_text(self.svg(), encoding="utf-8")
        (mmd_dir / f"{self.name}.mmd").write_text(self.mermaid(), encoding="utf-8")
        page = svg_dir / f"{self.name}.html"
        page.write_text(f'<!doctype html><html><head><meta charset="utf-8"><style>body{{margin:0;background:#fff}}'
                        f'</style></head><body>{self.svg()}</body></html>', encoding="utf-8")
        png = png_dir / f"{self.name}.png"
        with tempfile.TemporaryDirectory() as prof:
            subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                            f"--user-data-dir={prof}", "--force-device-scale-factor=2",
                            f"--window-size={self.w},{self.h}", f"--screenshot={png}", page.as_uri()],
                           check=True, capture_output=True, timeout=120)
        im = Image.open(png).convert("RGB")
        bbox = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
        if bbox:
            im = im.crop((max(bbox[0] - 24, 0), max(bbox[1] - 24, 0), min(bbox[2] + 24, im.width),
                          min(bbox[3] + 24, im.height)))
        im.save(png, optimize=True)
        page.unlink()
        return png, im.size
