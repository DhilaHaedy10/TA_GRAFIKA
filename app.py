"""
app.py  —  Aplikasi Grafika Komputer
═════════════════════════════════════
Mata Kuliah : Grafika Komputer — Semester Genap 2024/2025
Dosen       : Herry Sofyan, S.T., M.Kom.

Jalankan : python app.py
Modul    : app.py | models.py | transforms.py | renderer.py | constants.py
"""

import json
import math
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox

import customtkinter as ctk

from constants import (
    ACCENT, APP_AUTHOR, APP_TITLE, BG_APP, BG_CANVAS, BG_SECTION,
    BG_SIDEBAR, BORDER, CANVAS_H, CANVAS_W, LINE_DASHES, PURPLE, RED,
    REFLECTION_AXES, SHAPES, TEXT_BRIGHT, TEXT_DIM, TRANSFORMS,
)
from models import GrafisObjek
from renderer import Renderer, flat, oval_to_poly, rect_to_poly
from transforms import (
    apply_matrix, reflect_matrix, rotate_matrix,
    scale_matrix, skew_matrix, translate_matrix,
)

# ── CustomTkinter global setup ───────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Konstanta ukuran widget ───────────────────────────────────────────────────
BTN_H      = 34
ENTRY_H    = 32
COMBO_H    = 32
SIDEBAR_W  = 240
RIGHT_W    = 280
CORNER     = 8


# ═══════════════════════════════════════════════════════════════════════════════
#  KOMPONEN UI REUSABLE
# ═══════════════════════════════════════════════════════════════════════════════

def section_label(parent, text: str) -> ctk.CTkLabel:
    lbl = ctk.CTkLabel(parent, text=text,
                       font=ctk.CTkFont("Segoe UI", 11, "bold"),
                       text_color=TEXT_BRIGHT,
                       fg_color=BG_SECTION,
                       corner_radius=6, height=30,
                       anchor="w", padx=10)
    lbl.pack(fill="x", padx=8, pady=(10,4))
    return lbl


def dim_label(parent, text: str) -> ctk.CTkLabel:
    lbl = ctk.CTkLabel(parent, text=text,
                       font=ctk.CTkFont("Segoe UI", 9),
                       text_color=TEXT_DIM, anchor="w")
    lbl.pack(fill="x", padx=14, pady=(4,1))
    return lbl


def hint_label(parent, text: str) -> ctk.CTkLabel:
    lbl = ctk.CTkLabel(parent, text=text,
                       font=ctk.CTkFont("Consolas", 8),
                       text_color="#64748b", anchor="w",
                       justify="left", wraplength=220)
    lbl.pack(fill="x", padx=16, pady=(0,4))
    return lbl


def separator(parent):
    fr = ctk.CTkFrame(parent, height=1, fg_color=BORDER)
    fr.pack(fill="x", padx=8, pady=6)


def make_btn(parent, text, cmd, color=ACCENT,
             height=BTN_H, corner=CORNER) -> ctk.CTkButton:
    return ctk.CTkButton(parent, text=text, command=cmd,
                         fg_color=color, hover_color=_darken(color),
                         font=ctk.CTkFont("Segoe UI", 10, "bold"),
                         height=height, corner_radius=corner)


def make_entry(parent, var, width=None) -> ctk.CTkEntry:
    kw = {"textvariable": var, "height": ENTRY_H,
          "corner_radius": CORNER,
          "font": ctk.CTkFont("Consolas", 11)}
    if width:
        kw["width"] = width
    return ctk.CTkEntry(parent, **kw)


def make_combo(parent, var, values, cmd=None) -> ctk.CTkComboBox:
    cb = ctk.CTkComboBox(parent, variable=var, values=values,
                         height=COMBO_H, corner_radius=CORNER,
                         font=ctk.CTkFont("Segoe UI", 10),
                         dropdown_font=ctk.CTkFont("Segoe UI", 10),
                         state="readonly")
    if cmd:
        cb.configure(command=lambda v: cmd())
    cb.pack(fill="x", padx=10, pady=(0,4))
    return cb


def _darken(hex_color: str, factor=0.8) -> str:
    hex_color = hex_color.lstrip("#")
    r,g,b = (int(hex_color[i:i+2],16) for i in (0,2,4))
    return "#{:02x}{:02x}{:02x}".format(
        int(r*factor), int(g*factor), int(b*factor))


# ═══════════════════════════════════════════════════════════════════════════════
#  PANEL KIRI  —  Alat Gambar
# ═══════════════════════════════════════════════════════════════════════════════

class LeftPanel(ctk.CTkScrollableFrame):
    def __init__(self, master, app: "GrafikaApp"):
        super().__init__(master, width=SIDEBAR_W, corner_radius=0,
                         fg_color=BG_SIDEBAR,
                         scrollbar_button_color=BORDER,
                         scrollbar_button_hover_color=ACCENT)
        self.app = app
        self._build()

    def _build(self):
        app = self.app

        # ── Bentuk ─────────────────────────────────────────────────────────
        section_label(self, "🎨  Alat Gambar")

        dim_label(self, "Bentuk Objek")
        make_combo(self, app.current_shape, SHAPES,
                   cmd=app._on_shape_change)

        separator(self)

        # ── Warna ──────────────────────────────────────────────────────────
        dim_label(self, "Warna Isi (Fill)")
        app._fill_swatch = ColorSwatch(self, app.fill_color,
                                        lambda: app._pick_color("fill"))
        app._fill_swatch.pack(fill="x", padx=10, pady=(0,6))

        dim_label(self, "Warna Garis (Outline)")
        app._outline_swatch = ColorSwatch(self, app.outline_color,
                                           lambda: app._pick_color("outline"))
        app._outline_swatch.pack(fill="x", padx=10, pady=(0,6))

        separator(self)

        # ── Atribut garis ──────────────────────────────────────────────────
        dim_label(self, "Ketebalan Garis")
        lw_row = ctk.CTkFrame(self, fg_color="transparent")
        lw_row.pack(fill="x", padx=10, pady=(0,4))

        app._lw_slider = ctk.CTkSlider(
            lw_row, from_=1, to=14,
            variable=app.line_width_var,
            command=lambda v: app._lw_label.configure(
                text=str(int(float(v)))),
            progress_color=ACCENT, button_color=ACCENT,
            button_hover_color=_darken(ACCENT))
        app._lw_slider.pack(side="left", fill="x", expand=True, padx=(0,6))
        app._lw_label = ctk.CTkLabel(
            lw_row, text="2", width=24,
            font=ctk.CTkFont("Segoe UI", 10, "bold"),
            text_color=ACCENT)
        app._lw_label.pack(side="left")

        dim_label(self, "Tipe Garis")
        make_combo(self, app.line_dash_var, list(LINE_DASHES.keys()))

        separator(self)

        # ── Aksi cepat ────────────────────────────────────────────────────
        section_label(self, "⚡  Aksi Cepat")

        undo_redo = ctk.CTkFrame(self, fg_color="transparent")
        undo_redo.pack(fill="x", padx=10, pady=(0,4))
        undo_redo.columnconfigure((0,1), weight=1)

        make_btn(undo_redo, "↩ Undo", app._undo, "#334155", 32).grid(
            row=0, column=0, sticky="ew", padx=(0,2))
        make_btn(undo_redo, "↪ Redo", app._redo, "#334155", 32).grid(
            row=0, column=1, sticky="ew", padx=(2,0))

        make_btn(self, "🗑  Hapus Dipilih", app._delete_selected,
                 RED).pack(fill="x", padx=10, pady=2)
        make_btn(self, "🗑  Hapus Semua",  app._clear_all,
                 "#7f1d1d").pack(fill="x", padx=10, pady=(2,6))

        separator(self)

        # ── Petunjuk ──────────────────────────────────────────────────────
        section_label(self, "ℹ️  Petunjuk")
        tips = (
            "Klik + Drag  →  buat objek\n"
            "Klik objek  →  pilih / seleksi\n"
            "Ctrl+Klik  →  tambah ke seleksi\n"
            "Drag kosong  →  seleksi blok\n"
            "Ctrl+A  →  pilih semua\n"
            "Drag objek  →  pindahkan posisi\n"
            "Klik kosong  →  batalkan pilihan\n"
            "Double-klik  →  tutup Poligon\n"
            "Del  →  hapus objek dipilih\n"
            "Ctrl+Z / Y  →  Undo / Redo"
        )
        ctk.CTkLabel(self, text=tips,
                     font=ctk.CTkFont("Consolas", 8),
                     text_color=TEXT_DIM, justify="left",
                     anchor="w", padx=14
                     ).pack(fill="x", pady=(0,10))


# ═══════════════════════════════════════════════════════════════════════════════
#  COLOR SWATCH  — tombol preview warna
# ═══════════════════════════════════════════════════════════════════════════════

class ColorSwatch(ctk.CTkFrame):
    def __init__(self, master, color: str, cmd):
        super().__init__(master, fg_color="transparent")
        self._color = color
        self._cmd   = cmd

        self._preview = ctk.CTkLabel(
            self, text="", width=36, height=28,
            fg_color=color, corner_radius=6)
        self._preview.pack(side="left", padx=(0,8))

        self._hex_lbl = ctk.CTkLabel(
            self, text=color,
            font=ctk.CTkFont("Consolas", 9),
            text_color=TEXT_DIM)
        self._hex_lbl.pack(side="left", padx=(0,8))

        make_btn(self, "Pilih", cmd, "#334155", 28, 6
                 ).pack(side="right")

    def set_color(self, color: str):
        self._color = color
        self._preview.configure(fg_color=color)
        self._hex_lbl.configure(text=color)


# ═══════════════════════════════════════════════════════════════════════════════
#  PANEL KANAN  —  Transformasi + Daftar Objek
# ═══════════════════════════════════════════════════════════════════════════════

class RightPanel(ctk.CTkFrame):
    def __init__(self, master, app: "GrafikaApp"):
        super().__init__(master, width=RIGHT_W, corner_radius=0,
                         fg_color=BG_SIDEBAR)
        self.pack_propagate(False)
        self.app = app
        self._build()

    def _build(self):
        app = self.app

        # ── Transformasi ───────────────────────────────────────────────────
        tab = ctk.CTkTabview(self, height=420,
                             fg_color=BG_SIDEBAR,
                             segmented_button_fg_color=BG_SECTION,
                             segmented_button_selected_color=ACCENT,
                             segmented_button_unselected_color=BG_SECTION,
                             segmented_button_selected_hover_color=_darken(ACCENT),
                             text_color=TEXT_BRIGHT,
                             corner_radius=10)
        tab.pack(fill="x", padx=6, pady=6)

        tab.add("⚙ Transform")

        self._build_transform_tab(tab.tab("⚙ Transform"), app)

        # ── Daftar objek ──────────────────────────────────────────────────
        section_label(self, "📋  Daftar Objek")

        # Tombol layer order
        layer_row = ctk.CTkFrame(self, fg_color="transparent")
        layer_row.pack(fill="x", padx=8, pady=(0, 4))
        layer_row.columnconfigure((0, 1), weight=1)
        make_btn(layer_row, "⬆ Bring Front", app._bring_front,
                 "#1e3a5f", 28, 6).grid(row=0, column=0, sticky="ew", padx=(0, 2))
        make_btn(layer_row, "⬇ Send Back", app._send_back,
                 "#1e3a5f", 28, 6).grid(row=0, column=1, sticky="ew", padx=(2, 0))

        list_outer = ctk.CTkFrame(self, fg_color="transparent")
        list_outer.pack(fill="both", expand=True, padx=8, pady=(0,4))

        app.obj_listbox = tk.Listbox(
            list_outer,
            bg="#0f172a", fg=TEXT_BRIGHT,
            selectbackground=ACCENT, selectforeground="#ffffff",
            font=("Segoe UI", 12), relief="flat",
            highlightthickness=0, activestyle="none",
            bd=0, exportselection=False,
            selectmode=tk.EXTENDED,
        )
        sb = ctk.CTkScrollbar(list_outer,
                              command=app.obj_listbox.yview,
                              button_color=BORDER,
                              button_hover_color=ACCENT)
        sb.pack(side="right", fill="y")
        app.obj_listbox.config(yscrollcommand=sb.set)
        app.obj_listbox.pack(fill="both", expand=True)
        app.obj_listbox.bind("<<ListboxSelect>>", app._on_listbox_select)

    def _build_transform_tab(self, tab, app):
        dim_label(tab, "Jenis Transformasi")
        app.transform_var = tk.StringVar(value="Translasi")
        make_combo(tab, app.transform_var, TRANSFORMS,
                   cmd=app._update_transform_panel)

        app.tf_frame = ctk.CTkFrame(tab, fg_color="transparent")
        app.tf_frame.pack(fill="x")
        app._update_transform_panel()

        make_btn(tab, "▶  Terapkan Transformasi",
                 app._apply_transform, ACCENT
                 ).pack(fill="x", padx=6, pady=8)

# ═══════════════════════════════════════════════════════════════════════════════
#  PARAMETER PANEL (dinamis, di dalam tab Transform)
# ═══════════════════════════════════════════════════════════════════════════════

def build_param(parent, label: str, key: str, default: float,
                app: "GrafikaApp"):
    dim_label(parent, label)
    var = tk.DoubleVar(value=default)
    setattr(app, f"_pv_{key}", var)
    make_entry(parent, var).pack(fill="x", padx=10, pady=(0,4))


def build_radio_center(parent, app: "GrafikaApp"):
    dim_label(parent, "Titik Pusat")
    if not hasattr(app, "_center_var"):
        app._center_var = tk.StringVar(value="obj")
    rframe = ctk.CTkFrame(parent, fg_color="transparent")
    rframe.pack(fill="x", padx=10, pady=(0,6))
    for val, txt in [("obj","Pusat Objek"), ("canvas","Pusat Kanvas")]:
        ctk.CTkRadioButton(rframe, text=txt, value=val,
                           variable=app._center_var,
                           font=ctk.CTkFont("Segoe UI",9),
                           radiobutton_width=14, radiobutton_height=14,
                           border_width_checked=4
                           ).pack(side="left", padx=(0,12))


# ═══════════════════════════════════════════════════════════════════════════════
#  APLIKASI UTAMA
# ═══════════════════════════════════════════════════════════════════════════════

class GrafikaApp:
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

        # ── Drawing state ───────────────────────────────────────────────────
        self._temp_ids:   list  = []
        self._drag_start        = None
        self._poly_pts:   list  = []
        self._drawing_poly      = False

        # ── Move (drag objek) state ──────────────────────────────────────────
        self._move_obj          = None   # objek yang sedang di-drag
        self._move_last_xy      = None   # posisi mouse terakhir saat drag
        self._move_saved_history = False  # history disimpan sekali sebelum drag

        # ── Rubber-band selection state ──────────────────────────────────────
        self._rb_start          = None   # titik awal rubber-band
        self._rb_rect_id        = None   # canvas id kotak sementara

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
            targets = self.selected_set if self.selected_set else [self._move_obj]
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
            targets = self.selected_set if self.selected_set else [self._move_obj]
            self._move_obj     = None
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

    def _apply_transform(self):
        targets = self.selected_set if self.selected_set else (
            [self.selected] if self.selected else [])
        if not targets:
            messagebox.showwarning("Peringatan",
                                   "Pilih objek terlebih dahulu!"); return
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

    def _clear_all(self):
        if not self.objects: return
        if not messagebox.askyesno("Konfirmasi","Hapus semua objek?"): return
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

    def _about(self):
        messagebox.showinfo("Tentang",
            f"{APP_TITLE}\nDosen: {APP_AUTHOR}\n\n"
            "Fitur:\n"
            "  Output Primitif: Garis, Persegi, Persegi Panjang,\n"
            "    Lingkaran, Elips, Segitiga, Poligon Bebas\n\n"
            "  Atribut: Fill, Outline, Ketebalan, Tipe Garis\n\n"
            "  Transformasi 2D:\n"
            "    Translasi · Rotasi · Skala\n"
            "    Skew (Kiri/Kanan/Atas/Bawah)\n"
            "    Refleksi (Sumbu X/Y, y=x, y=-x, Garis Kustom)\n"
            "    Visualisasi Garis Cermin\n\n"
            "  Undo/Redo · Simpan/Buka (JSON)")


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    root = ctk.CTk()
    app  = GrafikaApp(root)
    root.mainloop()
