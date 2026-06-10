"""Interaksi menggambar pada kanvas."""

import math

from grafika.constants import LINE_DASHES
from grafika.models import GrafisObjek
from grafika.renderer import flat, oval_to_poly, rect_to_poly


class DrawingControllerMixin:
    def _on_shape_change(self):
        shape = self.current_shape.get()
        if shape == "Poligon Bebas":
            self._poly_pts.clear()
            self._drawing_poly = False
        self.status_var.set(f"Alat: {shape}  —  klik+drag untuk menggambar")

    def _on_press(self, event):
        shape = self.current_shape.get()
        x, y  = event.x, event.y
        ctrl  = (event.state & 0x0004) != 0   # Ctrl ditekan?

        if shape == "Pilih Objek":
            hit = self.canvas.find_overlapping(x - 4, y - 4, x + 4, y + 4)
            hit_obj = None
            if hit:
                for cid in reversed(hit):
                    for obj in reversed(self.objects):
                        if cid in obj.canvas_ids:
                            hit_obj = obj; break
                    if hit_obj:
                        break

            if hit_obj:
                if ctrl:
                    # Toggle objek dari/ke set
                    if hit_obj in self.selected_set:
                        self.selected_set.remove(hit_obj)
                        self.renderer.unhighlight(hit_obj)
                        self.selected = self.selected_set[-1] if self.selected_set else None
                    else:
                        self.selected_set.append(hit_obj)
                        self.selected = hit_obj
                    self._apply_multi_highlight()
                    self._sync_listbox_selection()
                    n = len(self.selected_set)
                    self._sel_info_var.set(f"  {n} objek dipilih")
                    self.status_var.set(f"Dipilih: {n} objek")
                else:
                    if hit_obj not in self.selected_set:
                        # Klik biasa pada objek baru → single select
                        self._deselect()
                        self._select_object(hit_obj)
                    # Mulai drag-move semua objek di set
                self._move_obj     = hit_obj
                self._move_targets = list(self.selected_set) if self.selected_set else [hit_obj]
                self._move_last_xy = (x, y)
                self._move_saved_history = False
                self.canvas.config(cursor="fleur")
            else:
                if not ctrl:
                    self._deselect()
                # Mulai rubber-band
                self._rb_start    = (x, y)
                self._rb_rect_id  = None
            return

        if shape == "Poligon Bebas":
            if not self._drawing_poly:
                self._poly_pts = [(x,y)]; self._drawing_poly = True
            else:
                self._poly_pts.append((x,y)); self._redraw_temp_poly()
            return

        self._drag_start = (x, y)

    def _on_drag(self, event):
        # ── Drag-move objek: geser semua objek di selected_set ───────────
        if self._move_obj is not None and self._move_last_xy is not None:
            dx = event.x - self._move_last_xy[0]
            dy = event.y - self._move_last_xy[1]
            if (dx or dy) and not self._move_saved_history:
                self._save_history()
                self._move_saved_history = True
            self._move_last_xy = (event.x, event.y)
            targets = self._move_targets or [self._move_obj]
            for obj in targets:
                self.renderer.move_item(obj, dx, dy)
            self._apply_multi_highlight()
            n = len(targets)
            info = f"  {n} objek  |  Δx={dx:+.0f}  Δy={dy:+.0f}" if n > 1 \
                   else f"  {self._move_obj.name}  |  Δx={dx:+.0f}  Δy={dy:+.0f}"
            self._sel_info_var.set(info)
            return

        # ── Rubber-band selection ─────────────────────────────────────────
        if self._rb_start is not None:
            x0, y0 = self._rb_start
            x1, y1 = event.x, event.y
            if self._rb_rect_id:
                self.canvas.delete(self._rb_rect_id)
            self._rb_rect_id = self.canvas.create_rectangle(
                x0, y0, x1, y1,
                outline="#a855f7", width=1, dash=(5,3),
                fill="#a855f720", tags="rubber_band")
            return

        # ── Gambar preview ────────────────────────────────────────────────
        if self._drag_start is None:
            return
        self._clear_temp()
        self._draw_preview(*self._drag_start, event.x, event.y)

    def _on_release(self, event):
        # ── Selesai drag-move ─────────────────────────────────────────────
        if self._move_obj is not None:
            self.canvas.config(cursor="crosshair")
            targets = self._move_targets or [self._move_obj]
            self._move_obj     = None
            self._move_targets = []
            self._move_last_xy = None
            for obj in targets:
                self.renderer.sync_coords(obj)
            self._apply_multi_highlight()
            if len(targets) == 1:
                self._sel_info_var.set(
                    f"  {targets[0].name}  |  fill {targets[0].fill}  "
                    f"outline {targets[0].outline}  lebar {targets[0].line_width}")
            else:
                self._sel_info_var.set(f"  {len(targets)} objek dipilih")
            return

        # ── Selesai rubber-band ───────────────────────────────────────────
        if self._rb_start is not None:
            if self._rb_rect_id:
                self.canvas.delete(self._rb_rect_id)
                self._rb_rect_id = None
            x0, y0 = self._rb_start
            x1, y1 = event.x, event.y
            self._rb_start = None

            if abs(x1-x0) > 4 or abs(y1-y0) > 4:
                rx0, rx1 = min(x0,x1), max(x0,x1)
                ry0, ry1 = min(y0,y1), max(y0,y1)
                ctrl = (event.state & 0x0004) != 0
                if not ctrl:
                    self._deselect()
                for obj in self.objects:
                    if not obj.canvas_ids: continue
                    coords = self.canvas.coords(obj.canvas_ids[0])
                    if not coords: continue
                    xs = coords[0::2]; ys = coords[1::2]
                    ox0,ox1 = min(xs),max(xs); oy0,oy1 = min(ys),max(ys)
                    # Objek harus sepenuhnya di dalam rubber-band
                    if ox0>=rx0 and ox1<=rx1 and oy0>=ry0 and oy1<=ry1:
                        if obj not in self.selected_set:
                            self.selected_set.append(obj)
                if self.selected_set:
                    self.selected = self.selected_set[-1]
                    self._apply_multi_highlight()
                    self._sync_listbox_selection()
                    n = len(self.selected_set)
                    self._sel_info_var.set(f"  {n} objek dipilih")
                    self.status_var.set(f"Seleksi blok: {n} objek dipilih")
            return

        shape = self.current_shape.get()
        if shape in ("Pilih Objek","Poligon Bebas"): return
        if self._drag_start is None: return

        x0,y0 = self._drag_start; x1,y1 = event.x, event.y
        self._clear_temp(); self._drag_start = None
        if abs(x1-x0)<3 and abs(y1-y0)<3: return

        self._save_history()
        pts = self._build_points(shape, x0,y0, x1,y1)
        obj = GrafisObjek(shape, pts,
                          fill=self.fill_color,
                          outline=self.outline_color,
                          line_width=int(self.line_width_var.get()),
                          line_dash=LINE_DASHES[self.line_dash_var.get()])
        self.objects.append(obj)
        self.renderer.render(obj, on_click=self._select_object)
        self._refresh_listbox()
        self._select_object(obj)
        self.status_var.set(f"✓ Objek '{obj.name}' dibuat.")

    def _on_double_click(self, event):
        if self.current_shape.get()=="Poligon Bebas" and self._drawing_poly:
            if len(self._poly_pts) >= 3:
                self._clear_temp(); self._drawing_poly = False
                self._save_history()
                obj = GrafisObjek("Poligon Bebas", self._poly_pts,
                                  fill=self.fill_color,
                                  outline=self.outline_color,
                                  line_width=int(self.line_width_var.get()),
                                  line_dash=LINE_DASHES[self.line_dash_var.get()])
                self.objects.append(obj)
                self.renderer.render(obj, on_click=self._select_object)
                self._refresh_listbox(); self._select_object(obj)
                self._poly_pts.clear()

    def _on_mouse_move(self, event):
        self._cursor_var.set(f"x={event.x}  y={event.y}")
        if self._drawing_poly and self._poly_pts:
            self._clear_temp()
            pts  = self._poly_pts + [(event.x, event.y)]
            f    = flat(pts)
            if len(f) >= 4:
                tid = self.canvas.create_line(
                    *f, fill=self.outline_color,
                    width=int(self.line_width_var.get()),
                    dash=LINE_DASHES[self.line_dash_var.get()],
                    capstyle="round", joinstyle="round",
                    tags="temp")
                self._temp_ids.append(tid)

    def _on_resize(self):
        # Throttle: batalkan jadwal sebelumnya, jadwalkan ulang 150ms kemudian
        if hasattr(self, "_resize_after_id") and self._resize_after_id:
            self.root.after_cancel(self._resize_after_id)
        self._resize_after_id = self.root.after(150, self.renderer.draw_grid)

    # ── Seleksi ───────────────────────────────────────────────────────────
    def _draw_preview(self, x0, y0, x1, y1):
        shape = self.current_shape.get()
        lw    = int(self.line_width_var.get())
        dash  = LINE_DASHES[self.line_dash_var.get()]
        fill, outline = self.fill_color, self.outline_color
        tid = None

        if shape == "Garis":
            tid = self.canvas.create_line(
                x0,y0,x1,y1, fill=outline, width=lw, dash=dash,
                capstyle="round", joinstyle="round", tags="temp")
        elif shape in ("Persegi","Persegi Panjang"):
            if shape=="Persegi":
                s=min(abs(x1-x0),abs(y1-y0))
                x1=x0+(s if x1>x0 else -s); y1=y0+(s if y1>y0 else -s)
            # Gambar sebagai polygon agar konsisten
            pts = rect_to_poly(x0,y0,x1,y1)
            tid = self.canvas.create_polygon(
                *flat(pts), fill=fill, outline=outline,
                width=lw, dash=dash, joinstyle="round", tags="temp")
        elif shape=="Lingkaran":
            r=math.hypot(x1-x0,y1-y0)
            pts=oval_to_poly(x0-r,y0-r,x0+r,y0+r)
            tid=self.canvas.create_polygon(
                *flat(pts), fill=fill, outline=outline,
                width=lw, dash=dash, joinstyle="round", tags="temp")
        elif shape=="Elips":
            pts=oval_to_poly(x0,y0,x1,y1)
            tid=self.canvas.create_polygon(
                *flat(pts), fill=fill, outline=outline,
                width=lw, dash=dash, joinstyle="round", tags="temp")
        elif shape=="Segitiga":
            pts=[(x0,y1),((x0+x1)//2,y0),(x1,y1)]
            tid=self.canvas.create_polygon(
                *flat(pts), fill=fill, outline=outline,
                width=lw, dash=dash, joinstyle="round", tags="temp")

        if tid: self._temp_ids.append(tid)

    def _build_points(self, shape, x0, y0, x1, y1):
        if shape == "Garis":          return [(x0,y0),(x1,y1)]
        elif shape == "Persegi":
            s=min(abs(x1-x0),abs(y1-y0))
            x1=x0+(s if x1>x0 else -s); y1=y0+(s if y1>y0 else -s)
            return rect_to_poly(x0,y0,x1,y1)
        elif shape == "Persegi Panjang": return rect_to_poly(x0,y0,x1,y1)
        elif shape == "Lingkaran":
            r=math.hypot(x1-x0,y1-y0)
            return oval_to_poly(x0-r,y0-r,x0+r,y0+r)
        elif shape == "Elips":        return oval_to_poly(x0,y0,x1,y1)
        elif shape == "Segitiga":     return [(x0,y1),((x0+x1)//2,y0),(x1,y1)]
        return [(x0,y0),(x1,y1)]

    def _clear_temp(self):
        for tid in self._temp_ids: self.canvas.delete(tid)
        self._temp_ids.clear()

    def _redraw_temp_poly(self):
        self._clear_temp()
        if len(self._poly_pts)>=2:
            f=flat(self._poly_pts)
            tid=self.canvas.create_line(*f, fill=self.outline_color,
                                        width=int(self.line_width_var.get()),
                                        capstyle="round", joinstyle="round",
                                        tags="temp")
            self._temp_ids.append(tid)

    # ══════════════════════════════════════════════════════════════════════════
    #  TERAPKAN TRANSFORMASI
    # ══════════════════════════════════════════════════════════════════════════

