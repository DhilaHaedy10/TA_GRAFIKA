"""Seleksi objek dan sinkronisasi daftar objek."""

from grafika.models import GrafisObjek


class SelectionControllerMixin:
    def _select_object(self, obj: GrafisObjek):
        """Single-select: bersihkan set lalu pilih 1 objek."""
        self._deselect()
        self.selected = obj
        self.selected_set = [obj]
        self.renderer.highlight(obj)
        self._sel_info_var.set(
            f"  {obj.name}  |  fill {obj.fill}  "
            f"outline {obj.outline}  lebar {obj.line_width}")
        for i,o in enumerate(self.objects):
            if o is obj:
                self.obj_listbox.selection_clear(0,"end")
                self.obj_listbox.selection_set(i)
                self.obj_listbox.see(i); break
        self.status_var.set(f"Dipilih: {obj.name}")

    def _apply_multi_highlight(self):
        """Terapkan highlight sesuai jumlah objek di selected_set."""
        if len(self.selected_set) == 1:
            self.renderer.highlight(self.selected_set[0])
        elif len(self.selected_set) > 1:
            self.renderer.highlight_multi(self.selected_set)
        else:
            self.renderer._clear_sel_box()

    def _sync_listbox_selection(self):
        """Sinkronkan highlight listbox dengan selected_set."""
        self.obj_listbox.selection_clear(0, "end")
        for obj in self.selected_set:
            for i, o in enumerate(self.objects):
                if o is obj:
                    self.obj_listbox.selection_set(i)
                    break

    def _select_all(self):
        """Pilih semua objek (Ctrl+A)."""
        if not self.objects: return
        self._deselect()
        self.selected_set = list(self.objects)
        self.selected = self.selected_set[-1]
        self._apply_multi_highlight()
        self._sync_listbox_selection()
        n = len(self.selected_set)
        self._sel_info_var.set(f"  {n} objek dipilih (semua)")
        self.status_var.set(f"✓ Semua {n} objek dipilih.")

    def _deselect(self):
        # Unhighlight semua yang ada di set
        for obj in self.selected_set:
            try: self.renderer.unhighlight(obj)
            except: pass
        if not self.selected_set and self.selected:
            try: self.renderer.unhighlight(self.selected)
            except: pass
        self.selected = None
        self.selected_set = []
        self.renderer._clear_sel_box()
        self._sel_info_var.set("Belum ada objek dipilih")

    def _on_listbox_select(self, _=None):
        sel = self.obj_listbox.curselection()
        if not sel: return
        # Deselect dulu tanpa mereset listbox
        for obj in self.selected_set:
            try: self.renderer.unhighlight(obj)
            except: pass
        self.renderer._clear_sel_box()
        self.selected_set = []
        for idx in sel:
            if 0 <= idx < len(self.objects):
                self.selected_set.append(self.objects[idx])
        if self.selected_set:
            self.selected = self.selected_set[-1]
            self._apply_multi_highlight()
            n = len(self.selected_set)
            if n == 1:
                obj = self.selected_set[0]
                self._sel_info_var.set(
                    f"  {obj.name}  |  fill {obj.fill}  "
                    f"outline {obj.outline}  lebar {obj.line_width}")
                self.status_var.set(f"Dipilih: {obj.name}")
            else:
                self._sel_info_var.set(f"  {n} objek dipilih")
                self.status_var.set(f"Dipilih: {n} objek")

    def _refresh_listbox(self):
        self.obj_listbox.delete(0,"end")
        for obj in self.objects:
            if obj in self.selected_set:
                mark = "●"
            else:
                mark = "○"
            self.obj_listbox.insert("end", f"  {mark}  {obj.name}")

    # ══════════════════════════════════════════════════════════════════════════
    #  PREVIEW DAN BUILD POINTS
    # ══════════════════════════════════════════════════════════════════════════

