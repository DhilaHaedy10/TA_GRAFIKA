"""constants.py — warna, ukuran, konfigurasi global."""

APP_TITLE  = "Grafika Komputer — Semester Genap 2024/2025"
APP_AUTHOR = "Herry Sofyan, S.T., M.Kom."

CANVAS_W = 1000
CANVAS_H = 700

# ── Palet warna (dark, selaras CustomTkinter) ────────────────────────────────
BG_APP      = "#1a1b2e"   # root window
BG_SIDEBAR  = "#16213e"   # panel kiri / kanan
BG_SECTION  = "#0f3460"   # header seksi
BG_CANVAS   = "#ffffff"   # kanvas gambar (putih bersih)
BG_ENTRY    = "#1a1b2e"

ACCENT      = "#4f8ef7"   # biru utama
ACCENT_HOVER= "#3a7de8"
PURPLE      = "#7c3aed"
GREEN       = "#22c55e"
RED         = "#ef4444"
AMBER       = "#f59e0b"
TEAL        = "#06b6d4"

TEXT_BRIGHT = "#f1f5f9"
TEXT_DIM    = "#94a3b8"
BORDER      = "#2d3561"

GRID_COLOR  = "#e2e8f0"
AXIS_COLOR  = "#94a3b8"

# ── Tipe garis ───────────────────────────────────────────────────────────────
LINE_DASHES: dict[str, tuple] = {
    "Solid":   (),
    "Dash":    (12, 5),
    "Dot":     (2,  5),
    "DashDot": (12, 5, 2, 5),
}

# ── Bentuk ───────────────────────────────────────────────────────────────────
SHAPES = [
    "Pilih Objek",
    "Garis",
    "Persegi",
    "Persegi Panjang",
    "Lingkaran",
    "Elips",
    "Segitiga",
    "Poligon Bebas",
]

# ── Transformasi ─────────────────────────────────────────────────────────────
TRANSFORMS = ["Translasi", "Rotasi", "Skala", "Skew", "Refleksi"]

REFLECTION_AXES = [
    "Sumbu X",
    "Sumbu Y",
    "y = x",
    "y = -x",
    "Garis Kustom (y = mx + b)",
]

ANIM_TYPES = [
    "Rotasi",
    "Translasi Kanan-Kiri",
    "Skala Pulse",
    "Skew Kiri-Kanan",
]

