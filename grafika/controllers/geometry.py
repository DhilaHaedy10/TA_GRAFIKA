"""Operasi geometri tambahan seperti area perpotongan."""

from tkinter import colorchooser, messagebox

from grafika.models import GrafisObjek


class GeometryControllerMixin:
    def _polygon_area(self, pts):
        if len(pts) < 3:
            return 0.0
        return sum(
            x1 * y2 - x2 * y1
            for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1])
        ) / 2

    def _line_intersection(self, p1, p2, p3, p4):
        x1, y1 = p1; x2, y2 = p2
        x3, y3 = p3; x4, y4 = p4
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(den) < 1e-9:
            return p2
        px = ((x1*y2 - y1*x2) * (x3 - x4) -
              (x1 - x2) * (x3*y4 - y3*x4)) / den
        py = ((x1*y2 - y1*x2) * (y3 - y4) -
              (y1 - y2) * (x3*y4 - y3*x4)) / den
        return (px, py)

    def _clip_polygon(self, subject, clip):
        if len(subject) < 3 or len(clip) < 3:
            return []
        clip_pts = list(clip)
        if self._polygon_area(clip_pts) < 0:
            clip_pts.reverse()

        def inside(p, a, b):
            return ((b[0] - a[0]) * (p[1] - a[1]) -
                    (b[1] - a[1]) * (p[0] - a[0])) >= -1e-9

        output = list(subject)
        for a, b in zip(clip_pts, clip_pts[1:] + clip_pts[:1]):
            input_pts = output
            output = []
            if not input_pts:
                break
            prev = input_pts[-1]
            for curr in input_pts:
                curr_in = inside(curr, a, b)
                prev_in = inside(prev, a, b)
                if curr_in:
                    if not prev_in:
                        output.append(self._line_intersection(prev, curr, a, b))
                    output.append(curr)
                elif prev_in:
                    output.append(self._line_intersection(prev, curr, a, b))
                prev = curr
        return output

    def _selected_area_objects(self):
        targets = self.selected_set if self.selected_set else (
            [self.selected] if self.selected else [])
        return [obj for obj in targets
                if obj and obj.shape != "Garis" and len(obj.points) >= 3]

    def _color_intersection(self):
        targets = self._selected_area_objects()
        if len(targets) < 2:
            messagebox.showwarning(
                "Perpotongan",
                "Pilih minimal 2 objek bidang yang saling bertumpuk.")
            return

        overlap = list(targets[0].points)
        for obj in targets[1:]:
            overlap = self._clip_polygon(overlap, obj.points)
            if len(overlap) < 3 or abs(self._polygon_area(overlap)) < 1:
                messagebox.showinfo(
                    "Perpotongan",
                    "Objek yang dipilih tidak memiliki area perpotongan.")
                return

        color = colorchooser.askcolor(
            color=self.fill_color,
            title="Pilih warna area perpotongan")[1]
        if not color:
            return

        self._save_history()
        overlap_obj = GrafisObjek(
            "Area Perpotongan",
            overlap,
            fill=color,
            outline=color,
            line_width=1,
            line_dash=())
        overlap_obj.name = f"Perpotongan #{overlap_obj.id}"
        self.objects.append(overlap_obj)
        self.renderer.render(overlap_obj, on_click=self._select_object)
        self.selected_set = [overlap_obj]
        self.selected = overlap_obj
        self._refresh_listbox()
        self._apply_multi_highlight()
        self._sync_listbox_selection()
        self._sel_info_var.set(f"  {overlap_obj.name}  |  fill {color}")
        self.status_var.set(
            f"✓ Area perpotongan {len(targets)} objek diberi warna.")

