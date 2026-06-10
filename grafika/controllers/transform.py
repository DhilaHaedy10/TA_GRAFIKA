"""Panel dan aksi transformasi objek."""

import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from grafika.constants import CANVAS_H, CANVAS_W, PURPLE, REFLECTION_AXES
from grafika.models import GrafisObjek
from grafika.transforms import (
    apply_matrix, reflect_matrix, rotate_matrix, scale_matrix, skew_matrix,
    translate_matrix,
)
from grafika.ui.components import (
    build_param, build_radio_center, dim_label, hint_label, make_btn,
    make_combo,
)


class TransformControllerMixin:
    def _update_transform_panel(self):
        for w in self.tf_frame.winfo_children():
            w.destroy()

        t = self.transform_var.get()

        if t == "Translasi":
            build_param(self.tf_frame, "tx  (+ kanan / - kiri)", "tx", 50, self)
            build_param(self.tf_frame, "ty  (+ bawah / - atas)", "ty", 50, self)

        elif t == "Rotasi":
            build_param(self.tf_frame, "Sudut (°) — + searah jarum jam", "angle", 45, self)
            build_radio_center(self.tf_frame, self)

        elif t == "Skala":
            build_param(self.tf_frame, "sx  (faktor skala sumbu X)", "sx", 1.5, self)
            build_param(self.tf_frame, "sy  (faktor skala sumbu Y)", "sy", 1.5, self)
            hint_label(self.tf_frame, "sx=sy → proporsional  |  <1 perkecil  |  >1 perbesar")
            build_radio_center(self.tf_frame, self)

        elif t == "Skew":
            build_param(self.tf_frame, "Skew X (°)", "shx", 0, self)
            build_param(self.tf_frame, "Skew Y (°)", "shy", 0, self)
            hint_label(self.tf_frame,
                       "X>0 → kanan  X<0 → kiri\nY>0 → bawah  Y<0 → atas")

            dim_label(self.tf_frame, "Preset Arah")
            pg1 = ctk.CTkFrame(self.tf_frame, fg_color="transparent")
            pg1.pack(fill="x", padx=8, pady=2)
            pg1.columnconfigure((0,1), weight=1)
            pg2 = ctk.CTkFrame(self.tf_frame, fg_color="transparent")
            pg2.pack(fill="x", padx=8, pady=2)
            pg2.columnconfigure((0,1), weight=1)

            def sp(shx, shy):
                self._set_pv("shx", shx); self._set_pv("shy", shy)

            make_btn(pg1,"← Kiri",  lambda:sp(-20,0),"#334155",28,6).grid(row=0,column=0,sticky="ew",padx=(0,2))
            make_btn(pg1,"→ Kanan", lambda:sp( 20,0),"#334155",28,6).grid(row=0,column=1,sticky="ew",padx=(2,0))
            make_btn(pg2,"↑ Atas",  lambda:sp(0,-20),"#334155",28,6).grid(row=0,column=0,sticky="ew",padx=(0,2))
            make_btn(pg2,"↓ Bawah", lambda:sp(0, 20),"#334155",28,6).grid(row=0,column=1,sticky="ew",padx=(2,0))

        elif t == "Refleksi":
            dim_label(self.tf_frame, "Sumbu Cermin")
            self._refl_var = tk.StringVar(value="Sumbu X")
            make_combo(self.tf_frame, self._refl_var, REFLECTION_AXES,
                       cmd=self._preview_mirror)

            build_param(self.tf_frame, "m  (kemiringan garis kustom)", "mir_m", 1.0, self)
            build_param(self.tf_frame, "b  (intercept garis kustom)",  "mir_b", 0.0, self)

            btn_row = ctk.CTkFrame(self.tf_frame, fg_color="transparent")
            btn_row.pack(fill="x", padx=8, pady=4)
            btn_row.columnconfigure((0,1), weight=1)
            make_btn(btn_row, "👁 Tampilkan", self._preview_mirror,
                     PURPLE, 30, 6).grid(row=0, column=0, sticky="ew", padx=(0,2))
            make_btn(btn_row, "✖ Sembunyikan", self.renderer.hide_mirror_line,
                     "#334155", 30, 6).grid(row=0, column=1, sticky="ew", padx=(2,0))

            make_btn(self.tf_frame, "🪞  Cerminkan Objek (Buat Salinan)",
                     self._mirror_selected, PURPLE).pack(
                     fill="x", padx=8, pady=(2, 6))

    def _preview_mirror(self):
        axis  = getattr(self, "_refl_var", tk.StringVar(value="Sumbu X")).get()
        m_val = self._pv("mir_m", 1.0)
        b_val = self._pv("mir_b", 0.0)
        self.renderer.draw_mirror_line(axis, m_val, b_val)

    # ── Param helpers ─────────────────────────────────────────────────────
    def _pv(self, key, fallback=0.0):
        try:    return getattr(self, f"_pv_{key}").get()
        except: return fallback

    def _set_pv(self, key, val):
        try: getattr(self, f"_pv_{key}").set(val)
        except: pass

    def _center_mode(self):
        return getattr(self, "_center_var", tk.StringVar(value="obj")).get()

    # ══════════════════════════════════════════════════════════════════════════
    #  MOUSE EVENTS
    # ══════════════════════════════════════════════════════════════════════════
    def _apply_transform(self):
        targets = self.selected_set if self.selected_set else (
            [self.selected] if self.selected else [])
        if not targets:
            messagebox.showwarning("Peringatan",
                                   "Pilih objek terlebih dahulu!"); return
        if self._anim_running:
            self._stop_animation()
        self._save_history()
        t   = self.transform_var.get()
        ccx,ccy = self._canvas_center()
        use_canvas = self._center_mode() == "canvas"
        w = self.canvas.winfo_width()  or CANVAS_W
        h = self.canvas.winfo_height() or CANVAS_H

        try:
            for obj in targets:
                cx, cy = obj.center()
                pcx = ccx if use_canvas else cx
                pcy = ccy if use_canvas else cy

                if t=="Translasi":
                    M=translate_matrix(self._pv("tx"), self._pv("ty"))
                elif t=="Rotasi":
                    M=rotate_matrix(self._pv("angle"), pcx, pcy)
                elif t=="Skala":
                    M=scale_matrix(self._pv("sx",1), self._pv("sy",1), pcx, pcy)
                elif t=="Skew":
                    M=skew_matrix(self._pv("shx"), self._pv("shy"), pcx, pcy)
                elif t=="Refleksi":
                    axis=self._refl_var.get()
                    M=reflect_matrix(axis, self._pv("mir_m",1),
                                      self._pv("mir_b",0),
                                      canvas_w=w, canvas_h=h)
                else: continue

                obj.points = apply_matrix(obj.points, M)
                self.renderer.render(obj, on_click=self._select_object)
        except Exception as e:
            messagebox.showerror("Error Parameter", str(e)); return

        self._refresh_listbox()
        self._apply_multi_highlight()
        n = len(targets)
        self.status_var.set(
            f"✓ Transformasi '{t}' diterapkan pada {n} objek.")

    # ══════════════════════════════════════════════════════════════════════════
    #  UNDO / REDO
    # ══════════════════════════════════════════════════════════════════════════

    def _mirror_selected(self):
        """Buat salinan objek yang sudah dicerminkan berdasarkan pengaturan Refleksi saat ini."""
        targets = self.selected_set if self.selected_set else (
            [self.selected] if self.selected else [])
        if not targets:
            messagebox.showwarning("Pencerminan", "Pilih objek terlebih dahulu!"); return
        # Pastikan transform panel dalam mode Refleksi agar _refl_var ada
        if not hasattr(self, "_refl_var"):
            messagebox.showwarning("Pencerminan",
                "Buka tab Transform → pilih 'Refleksi' terlebih dahulu\n"
                "agar sumbu cermin dapat ditentukan."); return
        self._save_history()
        axis = self._refl_var.get()
        m_val = self._pv("mir_m", 1.0)
        b_val = self._pv("mir_b", 0.0)
        w = self.canvas.winfo_width()  or CANVAS_W
        h = self.canvas.winfo_height() or CANVAS_H
        M = reflect_matrix(axis, m_val, b_val, canvas_w=w, canvas_h=h)

        clones = []
        for obj in targets:
            new_pts = apply_matrix(obj.points, M)
            clone = GrafisObjek(obj.shape, new_pts,
                                fill=obj.fill, outline=obj.outline,
                                line_width=obj.line_width, line_dash=obj.line_dash)
            clone.name = f"{obj.name} (cermin)"
            self.objects.append(clone)
            self.renderer.render(clone, on_click=self._select_object)
            clones.append(clone)

        self.selected_set = clones
        self.selected = clones[-1]
        self._refresh_listbox()
        self._apply_multi_highlight()
        self._sync_listbox_selection()
        self._sel_info_var.set(f"  {len(clones)} objek cermin dipilih")
        self.status_var.set(f"✓ {len(clones)} salinan cermin dibuat  [sumbu: {axis}].")

