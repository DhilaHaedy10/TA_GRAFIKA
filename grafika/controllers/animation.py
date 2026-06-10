"""Kontrol animasi objek terpilih."""

import math
from tkinter import messagebox

from grafika.constants import GREEN, RED
from grafika.transforms import (
    apply_matrix, rotate_matrix, scale_matrix, skew_matrix, translate_matrix,
)
from grafika.ui.components import _darken


class AnimationControllerMixin:
    def _toggle_animation(self):
        if self._anim_running:
            self._stop_animation()
        else:
            self._start_animation()

    def _start_animation(self):
        if not self.selected:
            messagebox.showwarning("Animasi", "Pilih objek terlebih dahulu!")
            return
        if len(self.selected_set) > 1:
            messagebox.showwarning(
                "Animasi",
                "Animasi hanya berjalan pada 1 objek.\n"
                "Objek aktif yang dipakai: " + self.selected.name)

        self._anim_running = True
        self._anim_step = 0
        self._anim_snapshot = self.selected.points[:]
        self.anim_btn.configure(text="■  Hentikan Animasi", fg_color=RED,
                                hover_color=_darken(RED))
        self.status_var.set(f"▶ Animasi berjalan: {self.selected.name}")
        self._anim_loop()

    def _stop_animation(self):
        self._anim_running = False
        if self._anim_after_id:
            self.root.after_cancel(self._anim_after_id)
            self._anim_after_id = None
        if self.selected and self._anim_snapshot:
            self.selected.points = self._anim_snapshot[:]
            self.renderer.render(self.selected, on_click=self._select_object)
            self._select_object(self.selected)
        self.anim_btn.configure(text="▶  Mulai Animasi", fg_color=GREEN,
                                hover_color=_darken(GREEN))
        self.status_var.set("■ Animasi dihentikan.")

    def _anim_loop(self):
        if not self._anim_running or not self.selected:
            return

        obj = self.selected
        atyp = self.anim_type_var.get()
        spd = float(self.anim_speed_var.get())
        st = self._anim_step

        if atyp == "Rotasi":
            M = rotate_matrix(spd * 0.4, *obj.center())
        elif atyp == "Translasi Kanan-Kiri":
            tx = spd * math.sin(math.radians(st * 3))
            M = translate_matrix(tx, 0)
        elif atyp == "Skala Pulse":
            f = 1 + 0.015 * spd * math.sin(math.radians(st * 4))
            M = scale_matrix(f, f, *obj.center())
        elif atyp == "Skew Kiri-Kanan":
            ang = spd * math.sin(math.radians(st * 3))
            M = skew_matrix(ang, 0, *obj.center())
        else:
            M = [[1,0,0],[0,1,0],[0,0,1]]

        obj.points = apply_matrix(obj.points, M)
        self.renderer.render(obj, on_click=self._select_object)
        self.renderer.highlight(obj)

        self._anim_step += 1
        interval = max(16, 60 - int(spd) * 2)
        self._anim_after_id = self.root.after(interval, self._anim_loop)

