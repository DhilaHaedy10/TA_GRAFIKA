"""Komponen UI reusable untuk aplikasi grafika."""

import tkinter as tk

import customtkinter as ctk

from grafika.constants import (
    ACCENT, ANIM_TYPES, BG_SECTION, BG_SIDEBAR, BORDER, GREEN,
    LINE_DASHES, PURPLE, RED, SHAPES, TEXT_BRIGHT, TEXT_DIM, TRANSFORMS,
)

BTN_H = 34
ENTRY_H = 32
COMBO_H = 32
SIDEBAR_W = 240
RIGHT_W = 280
CORNER = 8


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
        make_btn(self, "🎨  Warnai Perpotongan", app._color_intersection,
                 PURPLE).pack(fill="x", padx=10, pady=(2,6))

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
            "Pilih 2+ objek → warnai perpotongan\n"
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
        tab.add("Animasi")

        self._build_transform_tab(tab.tab("⚙ Transform"), app)
        self._build_anim_tab(tab.tab("Animasi"), app)

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
    def _build_anim_tab(self, tab, app):
        dim_label(tab, "Tipe Animasi")
        app.anim_type_var = tk.StringVar(value="Rotasi")
        make_combo(tab, app.anim_type_var, ANIM_TYPES)

        dim_label(tab, "Kecepatan")
        sp_row = ctk.CTkFrame(tab, fg_color="transparent")
        sp_row.pack(fill="x", padx=10, pady=(0,6))
        app._sp_lbl = ctk.CTkLabel(sp_row, text=" 5",
                                   width=28,
                                   font=ctk.CTkFont("Segoe UI",10,"bold"),
                                   text_color=ACCENT)
        app._sp_lbl.pack(side="right")
        ctk.CTkSlider(sp_row, from_=1, to=20,
                      variable=app.anim_speed_var,
                      command=lambda v: app._sp_lbl.configure(
                          text=f"{int(float(v)):2d}"),
                      progress_color=GREEN, button_color=GREEN,
                      button_hover_color=_darken(GREEN)
                      ).pack(side="left", fill="x", expand=True)

        app.anim_btn = make_btn(tab, "▶  Mulai Animasi",
                                app._toggle_animation, GREEN)
        app.anim_btn.pack(fill="x", padx=6, pady=4)
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
