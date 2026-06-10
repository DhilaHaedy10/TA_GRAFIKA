"""
renderer.py — rendering objek ke tkinter Canvas
"""
import math
import tkinter as tk
from models import GrafisObjek


# ─── Geometry helpers ────────────────────────────────────────────────────────

def oval_to_poly(x0, y0, x1, y1, n=48) -> list:
    """Elips/lingkaran → poligon n sisi (smooth, 48 cukup untuk tampilan)."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rx, ry = abs(x1 - x0) / 2, abs(y1 - y0) / 2
    return [
        (cx + rx * math.cos(2 * math.pi * i / n),
         cy + ry * math.sin(2 * math.pi * i / n))
        for i in range(n)
    ]


def rect_to_poly(x0, y0, x1, y1) -> list:
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def flat(pts) -> list:
    return [c for p in pts for c in p]


# ─── Renderer ────────────────────────────────────────────────────────────────

class Renderer:
    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self._sel_box_id = None   # id kotak seleksi (satu, bukan per-frame)

    # ── Render penuh (buat/ganti canvas item) ────────────────────────────
    def render(self, obj: GrafisObjek, on_click=None):
        """Hapus item lama dan buat baru. Panggil hanya saat objek benar-benar berubah bentuk/warna."""
        # Bersihkan selection box dulu agar id-nya tidak ikut terhapus
        self._clear_sel_box()

        for cid in obj.canvas_ids:
            self.canvas.delete(cid)
        obj.canvas_ids = []

        shape = obj.shape
        pts   = obj.points
        dash  = obj.line_dash   # tuple, bisa () untuk solid
        cid   = None
        cid_outline = None   # overlay garis outline untuk dash pada polygon

        if shape == "Garis":
            f = flat(pts)
            if len(f) >= 4:
                cid = self.canvas.create_line(
                    *f, fill=obj.outline,
                    width=obj.line_width, dash=dash,
                    capstyle="round", joinstyle="round")
        else:
            # Konversi bbox → polygon sekali saja
            if shape in ("Persegi", "Persegi Panjang") and len(pts) == 2:
                obj.points = rect_to_poly(*pts[0], *pts[1])
            elif shape in ("Lingkaran", "Elips") and len(pts) == 2:
                obj.points = oval_to_poly(*pts[0], *pts[1])

            f = flat(obj.points)
            if len(f) >= 6:
                # Polygon fill tanpa outline (outline digambar terpisah agar dash bekerja benar)
                cid = self.canvas.create_polygon(
                    *f, fill=obj.fill, outline="",
                    joinstyle="round", width=0)

                # Outline terpisah sebagai polyline tertutup — ini yang merender dash dengan benar
                f_closed = f + f[:2]   # tutup loop
                cid_outline = self.canvas.create_line(
                    *f_closed,
                    fill=obj.outline, width=obj.line_width,
                    dash=dash, capstyle="round", joinstyle="round")

        ids = [x for x in [cid, cid_outline] if x is not None]
        if ids:
            obj.canvas_ids = ids

    # ── Move cepat saat drag (TANPA delete/recreate) ─────────────────────
    def move_item(self, obj: GrafisObjek, dx: float, dy: float):
        """Geser canvas item langsung — O(1), tidak ada delete/create."""
        for cid in obj.canvas_ids:
            self.canvas.move(cid, dx, dy)

    # ── Update koordinat internal setelah drag selesai ───────────────────
    def sync_coords(self, obj: GrafisObjek):
        """Baca koordinat aktual dari canvas item dan simpan kembali ke obj.points."""
        if not obj.canvas_ids:
            return
        # Ambil dari item pertama (polygon fill atau line)
        cid    = obj.canvas_ids[0]
        ctype  = self.canvas.type(cid)
        coords = self.canvas.coords(cid)
        if not coords:
            return

        if ctype == "line":
            pts = [(coords[i], coords[i+1]) for i in range(0, len(coords), 2)]
            # Hapus titik penutup duplikat (loop-close) jika ada
            if len(pts) > 1 and pts[-1] == pts[0]:
                pts = pts[:-1]
            obj.points = pts
        elif ctype == "polygon":
            obj.points = [(coords[i], coords[i+1])
                          for i in range(0, len(coords), 2)]

    # ── Bring to front / Send to back ────────────────────────────────────
    def bring_front(self, obj: GrafisObjek):
        """Naikkan objek ke lapisan paling atas."""
        for cid in obj.canvas_ids:
            self.canvas.lift(cid)
        if self._sel_box_id:
            self.canvas.lift(self._sel_box_id)

    def send_back(self, obj: GrafisObjek):
        """Turunkan objek ke lapisan paling bawah (tapi tetap di atas grid)."""
        for cid in reversed(obj.canvas_ids):
            self.canvas.lower(cid)
        # Pastikan grid tetap di bawah semua objek
        self.canvas.lower("grid")

    # ── Highlight / unhighlight ───────────────────────────────────────────
    def highlight(self, obj: GrafisObjek):
        """Tampilkan kotak seleksi biru dashed di sekeliling 1 objek."""
        self._clear_sel_box()
        if not obj.canvas_ids:
            return
        cid = obj.canvas_ids[0]
        try:
            self.canvas.itemconfig(cid, width=obj.line_width + 2)
            coords = self.canvas.coords(cid)
            if coords:
                xs = coords[0::2]; ys = coords[1::2]
                x0, y0 = min(xs) - 6, min(ys) - 6
                x1, y1 = max(xs) + 6, max(ys) + 6
                self._sel_box_id = self.canvas.create_rectangle(
                    x0, y0, x1, y1,
                    outline="#4f8ef7", width=1,
                    dash=(5, 4), fill="",
                    tags="selection_box")
        except Exception:
            pass

    def highlight_multi(self, objs: list):
        """Highlight banyak objek: per-objek box cyan kecil + bounding box ungu besar."""
        self._clear_sel_box()
        if not objs:
            return

        all_xs, all_ys = [], []

        for obj in objs:
            if not obj.canvas_ids:
                continue
            cid = obj.canvas_ids[0]
            try:
                self.canvas.itemconfig(cid, width=obj.line_width + 2)
                coords = self.canvas.coords(cid)
                if not coords:
                    continue
                xs = coords[0::2]; ys = coords[1::2]
                all_xs.extend(xs); all_ys.extend(ys)
                # kotak kecil per-objek (teal)
                self.canvas.create_rectangle(
                    min(xs) - 4, min(ys) - 4,
                    max(xs) + 4, max(ys) + 4,
                    outline="#06b6d4", width=1,
                    dash=(4, 3), fill="",
                    tags="selection_box")
            except Exception:
                pass

        # Bounding box besar seluruh seleksi (ungu)
        if all_xs and all_ys:
            self._sel_box_id = self.canvas.create_rectangle(
                min(all_xs) - 10, min(all_ys) - 10,
                max(all_xs) + 10, max(all_ys) + 10,
                outline="#a855f7", width=2,
                dash=(8, 4), fill="",
                tags="selection_box")

    def unhighlight(self, obj: GrafisObjek):
        self._clear_sel_box()
        for cid in obj.canvas_ids:
            try:
                self.canvas.itemconfig(cid, width=obj.line_width)
            except Exception:
                pass

    def _clear_sel_box(self):
        if self._sel_box_id:
            self.canvas.delete(self._sel_box_id)
            self._sel_box_id = None
        self.canvas.delete("selection_box")

    # ── Grid + sumbu ──────────────────────────────────────────────────────
    def draw_grid(self, step=40,
                  grid_color="#e2e8f0", axis_color="#94a3b8"):
        self.canvas.delete("grid")
        w = self.canvas.winfo_width()  or 1000
        h = self.canvas.winfo_height() or 700
        cx, cy = w // 2, h // 2

        for x in range(0, w, step):
            col = axis_color if x == cx else grid_color
            self.canvas.create_line(x, 0, x, h, fill=col, width=1,
                                    tags="grid")
        for y in range(0, h, step):
            col = axis_color if y == cy else grid_color
            self.canvas.create_line(0, y, w, y, fill=col, width=1,
                                    tags="grid")

        self.canvas.create_text(cx + 10, 10, text="Y",
                                fill=axis_color, tags="grid",
                                font=("Segoe UI", 9, "bold"))
        self.canvas.create_text(w - 10, cy - 12, text="X",
                                fill=axis_color, tags="grid",
                                font=("Segoe UI", 9, "bold"))
        self.canvas.create_oval(cx-3, cy-3, cx+3, cy+3,
                                fill=axis_color, outline="", tags="grid")
        self.canvas.lower("grid")

    # ── Mirror line ───────────────────────────────────────────────────────
    def draw_mirror_line(self, axis, m=1.0, b=0.0):
        self.canvas.delete("mirror_line")
        w = self.canvas.winfo_width()  or 1000
        h = self.canvas.winfo_height() or 700
        cx, cy = w // 2, h // 2
        kw = dict(fill="#f59e0b", width=2, dash=(8, 4), tags="mirror_line")

        coords, label = None, ""
        if axis == "Sumbu X":
            coords = (0, cy, w, cy);           label = "— Sumbu X"
        elif axis == "Sumbu Y":
            coords = (cx, 0, cx, h);           label = "| Sumbu Y"
        elif axis == "y = x":
            s = min(w, h)
            coords = (cx-s//2, cy+s//2, cx+s//2, cy-s//2); label = "y = x"
        elif axis == "y = -x":
            s = min(w, h)
            coords = (cx-s//2, cy-s//2, cx+s//2, cy+s//2); label = "y = -x"
        else:
            yl = m * (0 - cx) + b + cy
            yr = m * (w - cx) + b + cy
            coords = (0, yl, w, yr);           label = f"y={m:.2f}x+{b:.2f}"

        if coords:
            self.canvas.create_line(*coords, **kw)
            mx = (coords[0] + coords[2]) // 2
            my = (coords[1] + coords[3]) // 2
            self.canvas.create_text(mx, my - 14, text=f"  {label}  ",
                                    fill="#f59e0b",
                                    font=("Segoe UI", 8, "bold"),
                                    tags="mirror_line")

    def hide_mirror_line(self):
        self.canvas.delete("mirror_line")
