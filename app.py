"""Entry point dan shell utama Aplikasi Grafika Komputer."""

import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from grafika.constants import (
    ACCENT, APP_AUTHOR, APP_TITLE, BG_APP, BG_CANVAS, BG_SECTION,
    BORDER, TEXT_BRIGHT, TEXT_DIM,
)
from grafika.controllers.animation import AnimationControllerMixin
from grafika.controllers.drawing import DrawingControllerMixin
from grafika.controllers.geometry import GeometryControllerMixin
from grafika.controllers.selection import SelectionControllerMixin
from grafika.controllers.state import StateCommandMixin
from grafika.controllers.transform import TransformControllerMixin
from grafika.models import GrafisObjek
from grafika.renderer import Renderer
from grafika.ui.components import LeftPanel, RightPanel

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class GrafikaApp(
    TransformControllerMixin, DrawingControllerMixin, SelectionControllerMixin,
    GeometryControllerMixin, AnimationControllerMixin, StateCommandMixin,
):
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.configure(fg_color=BG_APP)
        self.root.state("zoomed")
        self.root.minsize(1150, 700)

        # ── Data ────────────────────────────────────────────────────────────
        self.objects:      list[GrafisObjek] = []
        self.selected:     GrafisObjek | None = None   # objek utama (single/last)
        self.selected_set: list[GrafisObjek]  = []     # multi-select
        self.history:      list = []
        self.redo_stack:   list = []

        # ── Variabel UI ─────────────────────────────────────────────────────
        self.current_shape   = tk.StringVar(value="Pilih Objek")
        self.fill_color      = "#60a5fa"
        self.outline_color   = "#1e40af"
        self.line_width_var  = tk.DoubleVar(value=2)
        self.line_dash_var   = tk.StringVar(value="Solid")
        self.anim_speed_var  = tk.DoubleVar(value=5)

        # ── Drawing state ───────────────────────────────────────────────────
        self._temp_ids:   list  = []
        self._drag_start        = None
        self._poly_pts:   list  = []
        self._drawing_poly      = False

        # ── Move (drag objek) state ──────────────────────────────────────────
        self._move_obj          = None   # objek yang sedang di-drag
        self._move_targets      = []     # semua objek yang ikut pindah saat drag
        self._move_last_xy      = None   # posisi mouse terakhir saat drag
        self._move_saved_history = False  # history disimpan sekali sebelum drag

        # ── Rubber-band selection state ──────────────────────────────────────
        self._rb_start          = None   # titik awal rubber-band
        self._rb_rect_id        = None   # canvas id kotak sementara

        self._anim_running  = False
        self._anim_after_id = None
        self._anim_step     = 0
        self._anim_snapshot = []

        self._build_ui()

    # ══════════════════════════════════════════════════════════════════════════
    #  BUILD UI
    # ══════════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        self._build_menubar()

        # Wrapper utama
        main = ctk.CTkFrame(self.root, fg_color=BG_APP, corner_radius=0)
        main.pack(fill="both", expand=True)

        # Panel kiri
        self.left_panel = LeftPanel(main, self)
        self.left_panel.pack(side="left", fill="y", padx=(4,0), pady=4)

        # Kanvas tengah
        canvas_wrap = ctk.CTkFrame(main, fg_color="#2d3561",
                                   corner_radius=10, border_width=1,
                                   border_color=BORDER)
        canvas_wrap.pack(side="left", fill="both", expand=True,
                         padx=6, pady=4)

        self.canvas = tk.Canvas(
            canvas_wrap, bg=BG_CANVAS, cursor="crosshair",
            highlightthickness=0, bd=0,
        )

        # Renderer harus dibuat sebelum toolbar agar bisa direferensi
        self.renderer = Renderer(self.canvas)

        # Toolbar atas kanvas
        self._build_canvas_toolbar(canvas_wrap)

        self.canvas.pack(fill="both", expand=True,
                         padx=2, pady=(0,2))

        self.canvas.bind("<ButtonPress-1>",   self._on_press)
        self.canvas.bind("<B1-Motion>",       self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<Motion>",          self._on_mouse_move)
        self.canvas.bind("<Configure>",       lambda e: self._on_resize())

        self.root.after(100, self.renderer.draw_grid)

        # Panel kanan
        self.right_panel = RightPanel(main, self)
        self.right_panel.pack(side="right", fill="y", padx=(0,4), pady=4)

        # Status bar
        self.status_var = tk.StringVar(
            value="Selamat datang!  Pilih bentuk dan mulai menggambar.")
        status_bar = ctk.CTkFrame(self.root, height=28,
                                   fg_color="#0f172a", corner_radius=0)
        status_bar.pack(fill="x", side="bottom")
        ctk.CTkLabel(status_bar, textvariable=self.status_var,
                     font=ctk.CTkFont("Consolas", 9),
                     text_color="#7dd3fc", anchor="w"
                     ).pack(side="left", padx=12)

        # Koordinat kursor (kanan status bar)
        self._cursor_var = tk.StringVar(value="x=0  y=0")
        ctk.CTkLabel(status_bar, textvariable=self._cursor_var,
                     font=ctk.CTkFont("Consolas", 9),
                     text_color=TEXT_DIM
                     ).pack(side="right", padx=12)

        # Shortcuts
        self.root.bind("<Control-z>", lambda e: self._undo())
        self.root.bind("<Control-y>", lambda e: self._redo())
        self.root.bind("<Control-n>", lambda e: self._new_canvas())
        self.root.bind("<Control-s>", lambda e: self._save_json())
        self.root.bind("<Control-o>", lambda e: self._load_json())
        self.root.bind("<Delete>",    lambda e: self._delete_selected())
        self.root.bind("<Escape>",    lambda e: self._deselect())
        self.root.bind("<Prior>",     lambda e: self._bring_front())   # PgUp
        self.root.bind("<Next>",      lambda e: self._send_back())     # PgDn
        self.root.bind("<Control-a>", lambda e: self._select_all())    # Ctrl+A

    def _build_canvas_toolbar(self, parent):
        """Toolbar tipis di atas kanvas: info objek dipilih + tombol quick-action."""
        bar = ctk.CTkFrame(parent, height=36, fg_color=BG_SECTION,
                           corner_radius=0)
        bar.pack(fill="x", padx=2, pady=(2,0))
        bar.pack_propagate(False)

        ctk.CTkLabel(bar, text="  Kanvas",
                     font=ctk.CTkFont("Segoe UI", 10, "bold"),
                     text_color=TEXT_DIM
                     ).pack(side="left", padx=8)

        # Info objek dipilih
        self._sel_info_var = tk.StringVar(value="Belum ada objek dipilih")
        ctk.CTkLabel(bar, textvariable=self._sel_info_var,
                     font=ctk.CTkFont("Segoe UI", 9),
                     text_color=TEXT_DIM
                     ).pack(side="left", padx=20)

    def _build_menubar(self):
        menubar = tk.Menu(self.root, bg="#0f172a", fg=TEXT_BRIGHT,
                          activebackground=ACCENT, activeforeground="#fff",
                          relief="flat", bd=0)
        def _menu(label):
            m = tk.Menu(menubar, tearoff=0, bg="#0f172a", fg=TEXT_BRIGHT,
                        activebackground=ACCENT, activeforeground="#fff",
                        relief="flat")
            menubar.add_cascade(label=label, menu=m)
            return m

        f = _menu("File")
        f.add_command(label="  Baru                Ctrl+N", command=self._new_canvas)
        f.add_command(label="  Simpan (JSON)    Ctrl+S", command=self._save_json)
        f.add_command(label="  Buka (JSON)       Ctrl+O", command=self._load_json)
        f.add_separator()
        f.add_command(label="  Keluar", command=self.root.quit)

        e = _menu("Edit")
        e.add_command(label="  Undo   Ctrl+Z", command=self._undo)
        e.add_command(label="  Redo   Ctrl+Y", command=self._redo)
        e.add_separator()
        e.add_command(label="  Hapus Dipilih   Del", command=self._delete_selected)
        e.add_command(label="  Hapus Semua",         command=self._clear_all)
        e.add_separator()
        e.add_command(label="  ⬆ Bring to Front   PgUp", command=self._bring_front)
        e.add_command(label="  ⬇ Send to Back     PgDn", command=self._send_back)
        e.add_separator()
        e.add_command(label="  🪞 Cerminkan Objek", command=self._mirror_selected)

        h = _menu("Bantuan")
        h.add_command(label="  Tentang Aplikasi", command=self._about)

        self.root.configure(menu=menubar)

    # ══════════════════════════════════════════════════════════════════════════
    #  PANEL PARAMETER TRANSFORMASI  (dinamis)
    # ══════════════════════════════════════════════════════════════════════════

    def _about(self):
        messagebox.showinfo("Tentang",
            f"{APP_TITLE}\nDosen: {APP_AUTHOR}\n\n"
            "Fitur:\n"
            "  Output Primitif: Garis, Persegi, Persegi Panjang,\n"
            "    Lingkaran, Elips, Segitiga, Poligon Bebas\n\n"
            "  Atribut: Fill, Outline, Ketebalan, Tipe Garis\n\n"
            "  Area Perpotongan: warna khusus untuk objek bertumpuk\n\n"
            "  Transformasi 2D:\n"
            "    Translasi · Rotasi · Skala\n"
            "    Skew (Kiri/Kanan/Atas/Bawah)\n"
            "    Refleksi (Sumbu X/Y, y=x, y=-x, Garis Kustom)\n"
            "    Visualisasi Garis Cermin\n\n"
            "  Animasi: Rotasi, Translasi, Pulse, Skew\n"
            "  Undo/Redo · Simpan/Buka (JSON)")


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    root = ctk.CTk()
    app  = GrafikaApp(root)
    root.mainloop()
