"""Perintah edit, history, warna, dan simpan/buka kanvas."""

import json
from tkinter import colorchooser, filedialog, messagebox

from grafika.constants import CANVAS_H, CANVAS_W
from grafika.models import GrafisObjek


class StateCommandMixin:
    def _save_history(self):
        self.history.append([o.clone() for o in self.objects])
        self.redo_stack.clear()
        if len(self.history)>50: self.history.pop(0)

    def _undo(self):
        if not self.history:
            self.status_var.set("Tidak ada yang bisa di-undo."); return
        self.redo_stack.append([o.clone() for o in self.objects])
        self._restore_snapshot(self.history.pop())
        self.status_var.set("↩ Undo berhasil.")

    def _redo(self):
        if not self.redo_stack:
            self.status_var.set("Tidak ada yang bisa di-redo."); return
        self.history.append([o.clone() for o in self.objects])
        self._restore_snapshot(self.redo_stack.pop())
        self.status_var.set("↪ Redo berhasil.")

    def _restore_snapshot(self, snap):
        if self._anim_running:
            self._stop_animation()
        self._deselect()
        for o in self.objects:
            for cid in o.canvas_ids: self.canvas.delete(cid)
        self.objects = snap
        self.selected_set = []
        for o in self.objects:
            o.canvas_ids=[]
            self.renderer.render(o, on_click=self._select_object)
        self._refresh_listbox()

    # ══════════════════════════════════════════════════════════════════════════
    #  EDIT COMMANDS
    # ══════════════════════════════════════════════════════════════════════════

    def _delete_selected(self):
        targets = self.selected_set if self.selected_set else (
            [self.selected] if self.selected else [])
        if not targets: return
        if self._anim_running:
            self._stop_animation()
        self._save_history()
        for obj in targets:
            for cid in obj.canvas_ids: self.canvas.delete(cid)
            if obj in self.objects: self.objects.remove(obj)
        n = len(targets)
        self.selected = None
        self.selected_set = []
        self.renderer._clear_sel_box()
        self._refresh_listbox()
        self._sel_info_var.set("Belum ada objek dipilih")
        self.status_var.set(f"🗑 {n} objek dihapus.")

    def _bring_front(self):
        targets = self.selected_set if self.selected_set else (
            [self.selected] if self.selected else [])
        if not targets:
            self.status_var.set("⚠ Pilih objek terlebih dahulu."); return
        self._save_history()
        for obj in targets:
            self.objects.remove(obj)
            self.objects.append(obj)
            self.renderer.bring_front(obj)
        self._refresh_listbox()
        self._apply_multi_highlight()
        n = len(targets)
        self.status_var.set(f"⬆ {n} objek dipindahkan ke depan.")

    def _send_back(self):
        targets = self.selected_set if self.selected_set else (
            [self.selected] if self.selected else [])
        if not targets:
            self.status_var.set("⚠ Pilih objek terlebih dahulu."); return
        self._save_history()
        for obj in reversed(targets):
            self.objects.remove(obj)
            self.objects.insert(0, obj)
            self.renderer.send_back(obj)
        self._refresh_listbox()
        self._apply_multi_highlight()
        n = len(targets)
        self.status_var.set(f"⬇ {n} objek dipindahkan ke belakang.")

    def _clear_all(self):
        if not self.objects: return
        if not messagebox.askyesno("Konfirmasi","Hapus semua objek?"): return
        if self._anim_running:
            self._stop_animation()
        self._save_history(); self._deselect()
        for o in self.objects:
            for cid in o.canvas_ids: self.canvas.delete(cid)
        self.objects.clear(); self.selected_set = []; self._refresh_listbox()
        self.status_var.set("Semua objek dihapus.")

    def _new_canvas(self):
        if self._clear_canvas(confirm=True, reset_ids=True):
            self.status_var.set("Kanvas baru.")

    def _clear_canvas(self, confirm=False, reset_ids=True):
        if confirm and self.objects:
            if not messagebox.askyesno("Baru","Hapus semua dan mulai kanvas baru?"):
                return False
        if self._anim_running:
            self._stop_animation()
        self._deselect()
        for o in self.objects:
            for cid in o.canvas_ids: self.canvas.delete(cid)
        self.objects.clear(); self.history.clear(); self.redo_stack.clear()
        self.selected_set = []
        self._refresh_listbox()
        if reset_ids:
            GrafisObjek._id_counter=0
        return True

    # ── Warna (update objek dipilih langsung) ─────────────────────────────
    def _pick_color(self, which):
        init = self.fill_color if which=="fill" else self.outline_color
        col  = colorchooser.askcolor(color=init,
                                      title=f"Pilih warna {which}")[1]
        if not col: return
        if which=="fill":
            self.fill_color=col; self._fill_swatch.set_color(col)
        else:
            self.outline_color=col; self._outline_swatch.set_color(col)
        targets = self.selected_set if self.selected_set else (
            [self.selected] if self.selected else [])
        if targets:
            self._save_history()
            for obj in targets:
                if which=="fill": obj.fill=col
                else:             obj.outline=col
                self.renderer.render(obj, on_click=self._select_object)
            self._apply_multi_highlight()

    # ── Simpan / Buka ─────────────────────────────────────────────────────
    def _save_json(self):
        path=filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON","*.json"),("Semua","*.*")],
            title="Simpan Kanvas")
        if not path: return
        with open(path,"w",encoding="utf-8") as f:
            json.dump([o.to_dict() for o in self.objects], f,
                      indent=2, ensure_ascii=False)
        self.status_var.set(f"✓ Disimpan → {path}")

    def _load_json(self):
        path=filedialog.askopenfilename(
            filetypes=[("JSON","*.json"),("Semua","*.*")],
            title="Buka Kanvas")
        if not path: return
        try:
            with open(path,encoding="utf-8") as f: data=json.load(f)
        except Exception as e:
            messagebox.showerror("Error",str(e)); return
        self._clear_canvas(confirm=False, reset_ids=True)
        for d in data:
            o=GrafisObjek.from_dict(d)
            self.objects.append(o)
            self.renderer.render(o, on_click=self._select_object)
        self._refresh_listbox()
        self.status_var.set(f"✓ Dimuat ← {path}  ({len(self.objects)} objek)")

    # ── Utils ─────────────────────────────────────────────────────────────
    def _canvas_center(self):
        w=self.canvas.winfo_width()  or CANVAS_W
        h=self.canvas.winfo_height() or CANVAS_H
        return w//2, h//2

