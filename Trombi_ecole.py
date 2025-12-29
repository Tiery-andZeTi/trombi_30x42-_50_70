import os
import re
import sys
from math import floor
from dataclasses import dataclass
from typing import List, Tuple, Optional

from PIL import Image, ImageOps, ImageFilter

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
except Exception:
    tk = None  # UI optional when running headless

# =========================
# 1) CONSTANTES GLOBALES
# =========================
# Formats (cm) à 300 DPI (horizontaux)
FORMATS_PX = {
    "42x30": (4961, 3543),
    "70x50": (8268, 5906),
}

# Paramètres fixes
MARGE_EXTERIEURE_PX = 100
GOUTTIERE_PX = 30
RATIO_VIGNETTE = 2 / 3  # w / h (cellule théorique 2:3, sans crop)
CADRE_BORDURE_PX = 6
CADRE_COULEUR = "black"
DPI = 300

# Zone-titre (proportionnelle)
TITLE_LEFT_PCT = 0.22
TITLE_WIDTH_PCT = 0.56
TITLE_WH_RATIO = 6.0  # H = W / 6
TITLE_BOTTOM_PCT = 0.35

# Unsharp (léger)
USM_RADIUS = 0.6
USM_AMOUNT = 0.7
USM_THRESHOLD = 2

# Mode mémoire basse : traite image par image (recommandé)
LOW_MEMORY_MODE = True

# =========================
# 2) UTILITAIRES
# =========================


def longest_digit_seq(s: str) -> Optional[Tuple[int, int, str]]:
    matches = list(re.finditer(r"(\d+)", s))
    if not matches:
        return None
    matches.sort(key=lambda m: (-len(m.group(1)), m.start()))
    m = matches[0]
    seq = m.group(1)
    try:
        val = int(seq)
    except ValueError:
        val = 0
    return (len(seq), val, seq)


def natural_sort_key(filename: str) -> Tuple[int, int, str]:
    base = os.path.basename(filename)
    lds = longest_digit_seq(base)
    if lds is None:
        return (1, 0, base.lower())
    _, num, _ = lds
    return (0, num, base.lower())


def list_images_non_recursive(folder: str) -> List[str]:
    exts = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}
    paths = []
    try:
        for name in os.listdir(folder):
            p = os.path.join(folder, name)
            if os.path.isfile(p) and os.path.splitext(name)[1] in exts:
                paths.append(p)
    except FileNotFoundError:
        return []
    paths.sort(key=natural_sort_key)
    return paths


def is_readable_image(path: str) -> bool:
    try:
        with Image.open(path) as im:
            im.verify()  # validation rapide sans décoder entièrement
        return True
    except Exception:
        return False


@dataclass
class Rect:
    x0: int
    y0: int
    x1: int
    y1: int

    @property
    def w(self) -> int:
        return max(0, self.x1 - self.x0)

    @property
    def h(self) -> int:
        return max(0, self.y1 - self.y0)


# =========================
# 3) CALCUL ZONE-TITRE & AIRES
# =========================


def compute_title_rect(W: int, H: int) -> Rect:
    x_t0 = int(round(TITLE_LEFT_PCT * W))
    W_t = int(round(TITLE_WIDTH_PCT * W))
    H_t = int(round(W_t / TITLE_WH_RATIO))
    y_t1 = int(round(TITLE_BOTTOM_PCT * H))
    y_t0 = y_t1 - H_t
    x_t1 = x_t0 + W_t
    return Rect(x_t0, y_t0, x_t1, y_t1)


def intersect(a: Rect, b: Rect) -> Rect:
    return Rect(max(a.x0, b.x0), max(a.y0, b.y0), min(a.x1, b.x1), min(a.y1, b.y1))


def compute_zones(W: int, H: int) -> Tuple[Rect, Rect, Rect, Rect]:
    title = compute_title_rect(W, H)
    area = Rect(
        MARGE_EXTERIEURE_PX,
        MARGE_EXTERIEURE_PX,
        W - MARGE_EXTERIEURE_PX,
        H - MARGE_EXTERIEURE_PX,
    )

    top = intersect(Rect(area.x0, area.y0, area.x1, min(title.y0, area.y1)), area)
    left = intersect(
        Rect(
            area.x0,
            max(title.y0, area.y0),
            max(title.x0, area.x0),
            min(title.y1, area.y1),
        ),
        area,
    )
    right = intersect(
        Rect(
            min(title.x1, area.x1),
            max(title.y0, area.y0),
            area.x1,
            min(title.y1, area.y1),
        ),
        area,
    )
    bottom = intersect(Rect(area.x0, max(title.y1, area.y0), area.x1, area.y1), area)

    return top, left, right, bottom


# =========================
# 4) BINARY SEARCH HAUTEUR h
# =========================


def zone_capacity(rect: Rect, w_eff_cell: int, h_eff_cell: int) -> Tuple[int, int, int]:
    if rect.w <= 0 or rect.h <= 0 or w_eff_cell <= 0 or h_eff_cell <= 0:
        return 0, 0, 0
    cols = max(0, (rect.w + GOUTTIERE_PX) // (w_eff_cell + GOUTTIERE_PX))
    rows = max(0, (rect.h + GOUTTIERE_PX) // (h_eff_cell + GOUTTIERE_PX))
    return cols, rows, cols * rows


def total_capacity(
    W: int, H: int, h_cell: int
) -> Tuple[int, Tuple[Tuple[int, int, int], ...]]:
    w_cell = int(round(RATIO_VIGNETTE * h_cell))
    w_eff_cell = w_cell + 2 * CADRE_BORDURE_PX
    h_eff_cell = h_cell + 2 * CADRE_BORDURE_PX

    top, left, right, bottom = compute_zones(W, H)
    caps = (
        zone_capacity(top, w_eff_cell, h_eff_cell),
        zone_capacity(left, w_eff_cell, h_eff_cell),
        zone_capacity(right, w_eff_cell, h_eff_cell),
        zone_capacity(bottom, w_eff_cell, h_eff_cell),
    )
    total = sum(c for _, _, c in caps)
    return total, caps


def find_best_cell_height(
    W: int, H: int, n_images: int
) -> Tuple[int, Tuple[Tuple[int, int, int], ...]]:
    h_min = 20
    top, left, right, bottom = compute_zones(W, H)
    h_max_plausible = max(top.h, left.h, right.h, bottom.h)
    h_max = max(h_min, h_max_plausible)

    best_h = h_min
    best_caps = ((0, 0, 0),) * 4

    lo, hi = h_min, h_max
    while lo <= hi:
        mid = (lo + hi) // 2
        tot, caps = total_capacity(W, H, mid)
        if tot >= n_images:
            best_h, best_caps = mid, caps
            lo = mid + 1
        else:
            hi = mid - 1
    return best_h, best_caps


# =========================
# 5) PLACEMENT DANS LES ZONES
# =========================


def compute_zone_positions(
    rect: Rect, w_eff_cell: int, h_eff_cell: int, count: int
) -> List[Tuple[int, int]]:
    positions: List[Tuple[int, int]] = []
    if rect.w <= 0 or rect.h <= 0 or count <= 0:
        return positions

    cols = max(0, (rect.w + GOUTTIERE_PX) // (w_eff_cell + GOUTTIERE_PX))
    rows = max(0, (rect.h + GOUTTIERE_PX) // (h_eff_cell + GOUTTIERE_PX))
    cap = cols * rows
    if cols <= 0 or rows <= 0 or cap == 0:
        return positions

    n_to_place = min(count, cap)

    # Nombre de lignes réellement nécessaires
    full_rows, rem = divmod(n_to_place, cols)
    used_rows = full_rows + (1 if rem > 0 else 0)

    # Start x,y pour centrer avec gouttière standard
    total_width = cols * w_eff_cell + (cols - 1) * GOUTTIERE_PX
    total_height = used_rows * h_eff_cell + (used_rows - 1) * GOUTTIERE_PX
    x_start = rect.x0 + max(0, (rect.w - total_width) // 2)
    y_start = rect.y0 + max(0, (rect.h - total_height) // 2)

    placed = 0
    for row in range(used_rows):
        if row < full_rows:
            n_in_row = cols
        else:
            n_in_row = rem if rem > 0 else cols

        # Justification horizontale si dernière ligne partielle
        if row == used_rows - 1 and n_in_row < cols:
            total_cells_w = n_in_row * w_eff_cell
            n_spaces = max(1, n_in_row - 1)
            gouttiere = max(GOUTTIERE_PX, (rect.w - total_cells_w) // n_spaces)
            row_width = total_cells_w + (n_in_row - 1) * gouttiere
            x_row = rect.x0 + max(0, (rect.w - row_width) // 2)
        else:
            gouttiere = GOUTTIERE_PX
            row_width = cols * w_eff_cell + (cols - 1) * gouttiere
            x_row = rect.x0 + max(0, (rect.w - row_width) // 2)

        y = y_start + row * (h_eff_cell + GOUTTIERE_PX)
        x = x_row
        for _ in range(n_in_row):
            positions.append((x, y))
            placed += 1
            if placed >= n_to_place:
                break
            x += w_eff_cell + gouttiere
        if placed >= n_to_place:
            break

    return positions


# =========================
# 6) RENDU VIGNETTE (cadre collé à la photo)
# =========================


def build_block_with_tight_frame(
    img: Image.Image, w_cell: int, h_cell: int
) -> Image.Image:
    """
    Crée un bloc (image redimensionnée + cadre noir collé à l'image) sans remplir la cellule 2:3.
    Le bloc peut donc être plus petit que la cellule. On le centrera dans la cellule au collage.
    """
    src = img
    # Convertir si besoin
    if src.mode not in ("RGB", "RGBA"):
        src = src.convert("RGB")

    # Pour limiter la RAM/IO, si JPEG on peut demander un décodage plus proche de la cible
    try:
        if hasattr(img, "format") and img.format == "JPEG":
            img.draft("RGB", (w_cell, h_cell))
    except Exception:
        pass

    # Fit proportionnel dans (w_cell, h_cell)
    scale = min(w_cell / src.width, h_cell / src.height)
    new_w = max(1, int(round(src.width * scale)))
    new_h = max(1, int(round(src.height * scale)))

    resized = src.resize((new_w, new_h), Image.LANCZOS)

    # Sharpen léger
    resized = resized.filter(
        ImageFilter.UnsharpMask(
            radius=USM_RADIUS, percent=int(USM_AMOUNT * 100), threshold=USM_THRESHOLD
        )
    )

    # Ajouter cadre noir collé à l'image (autour du contenu)
    block = ImageOps.expand(resized, border=CADRE_BORDURE_PX, fill=CADRE_COULEUR)

    # Le block est en RGB par défaut -> pour collage avec transparence, on convertit en RGBA avec alpha opaque
    if block.mode != "RGBA":
        block = block.convert("RGBA")

    return block


# =========================
# 7) EXPORT PRINCIPAL (streaming low-memory)
# =========================


def export_trombi(folder: str, fmt_key: str, console_mode: bool = False) -> str:
    if fmt_key not in FORMATS_PX:
        raise ValueError(f"Format inconnu: {fmt_key}")

    W, H = FORMATS_PX[fmt_key]
    files_all = list_images_non_recursive(folder)
    if not files_all:
        raise RuntimeError("Dossier vide ou introuvable.")

    # Filtrer fichiers lisibles sans décoder entièrement
    readable_paths: List[str] = []
    bad_files: List[str] = []
    for p in files_all:
        if is_readable_image(p):
            readable_paths.append(p)
        else:
            bad_files.append(os.path.basename(p))

    N = len(readable_paths)
    if N == 0:
        raise RuntimeError("Aucune image lisible dans le dossier.")

    # Calcul taille de cellule (théorique 2:3) par binary search
    h_cell, caps = find_best_cell_height(W, H, N)
    w_cell = int(round(RATIO_VIGNETTE * h_cell))
    w_eff_cell = w_cell + 2 * CADRE_BORDURE_PX
    h_eff_cell = h_cell + 2 * CADRE_BORDURE_PX

    # Zones et répartitions
    top, left, right, bottom = compute_zones(W, H)
    caps_values = [c for (_, _, c) in caps]

    remaining = N
    zone_counts = [0, 0, 0, 0]
    for i in range(4):
        take = min(remaining, caps_values[i])
        zone_counts[i] = take
        remaining -= take

    # Positions des cellules (positions du coin supérieur gauche de la *cellule*)
    positions_top = compute_zone_positions(top, w_eff_cell, h_eff_cell, zone_counts[0])
    positions_left = compute_zone_positions(
        left, w_eff_cell, h_eff_cell, zone_counts[1]
    )
    positions_right = compute_zone_positions(
        right, w_eff_cell, h_eff_cell, zone_counts[2]
    )
    positions_bottom = compute_zone_positions(
        bottom, w_eff_cell, h_eff_cell, zone_counts[3]
    )
    all_cell_positions = (
        positions_top + positions_left + positions_right + positions_bottom
    )

    # Canevas final (transparent)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # Boucle streaming : ouvrir -> transformer -> encadrer -> coller -> fermer
    placed = 0
    for img_path, cell_pos in zip(readable_paths, all_cell_positions):
        try:
            with Image.open(img_path) as im:
                # Appliquer orientation EXIF juste avant usage
                im = ImageOps.exif_transpose(im)

                # Construire le bloc (image redimensionnée + cadre collé)
                block = build_block_with_tight_frame(im, w_cell, h_cell)

                # Centrer le bloc dans la cellule (w_eff_cell x h_eff_cell)
                bx, by = block.size
                cx, cy = cell_pos
                x = cx + max(0, (w_eff_cell - bx) // 2)
                y = cy + max(0, (h_eff_cell - by) // 2)

                # Collage: utiliser paste avec masque alpha (économe en RAM)
                canvas.paste(block, (x, y), block)
                placed += 1
        except Exception:
            bad_files.append(os.path.basename(img_path))

    # Export PNG 300 DPI (sans optimize pour la vitesse)
    parent = os.path.basename(os.path.dirname(os.path.abspath(folder))) or "export"
    out_name = f"trombi_{fmt_key}_{parent}.png"
    out_path = os.path.join(folder, out_name)
    try:
        # compress_level: 0 (rapide, gros fichier) -> 9 (lent, petit). Choix médian 6.
        canvas.save(out_path, format="PNG", dpi=(DPI, DPI), compress_level=6)
    except Exception as e:
        raise RuntimeError(f"Erreur d’export PNG: {e}")

    summary = (
        f"Export: {out_path}\n"
        f"Format: {W}×{H}px @ {DPI} DPI\n"
        f"Images placées: {placed} (ignorées: {len(bad_files)})\n"
        f"Cellule 2:3 (hors cadre): {h_cell}×{w_cell}px (h×w)\n"
        f"Cellule 2:3 (avec cadre): {h_eff_cell}×{w_eff_cell}px (h×w)\n"
        f"Bloc moyen ≈ image redimensionnée + cadre (centré dans la cellule)"
    )

    if bad_files:
        summary += "\nFichiers ignorés: " + ", ".join(bad_files[:10])
        if len(bad_files) > 10:
            summary += f" … (+{len(bad_files) - 10})"

    return summary


# =========================
# 8) UI TKINTER (identique, sans alerte <300 px)
# =========================


class App:
    def __init__(self, root):
        self.root = root
        root.title("Trombi École V0.2")
        root.geometry("520x220")

        self.folder_var = tk.StringVar()
        self.format_var = tk.StringVar(value="42x30")
        self.progress_var = tk.StringVar(value="Prêt.")

        frm = tk.Frame(root, padx=10, pady=10)
        frm.pack(fill=tk.BOTH, expand=True)

        row = 0
        tk.Label(frm, text="Dossier d’images:").grid(row=row, column=0, sticky="w")
        tk.Entry(frm, textvariable=self.folder_var, width=48).grid(
            row=row, column=1, padx=6
        )
        tk.Button(frm, text="Parcourir…", command=self.choose_folder).grid(
            row=row, column=2
        )
        row += 1

        tk.Label(frm, text="Format:").grid(row=row, column=0, sticky="w", pady=(8, 0))
        tk.OptionMenu(frm, self.format_var, *FORMATS_PX.keys()).grid(
            row=row, column=1, sticky="w", pady=(8, 0)
        )
        row += 1

        tk.Button(frm, text="Générer", command=self.on_generate, width=18).grid(
            row=row, column=1, pady=14
        )
        row += 1

        tk.Label(frm, textvariable=self.progress_var, fg="#444").grid(
            row=row, column=0, columnspan=3, sticky="w"
        )

    def choose_folder(self):
        folder = filedialog.askdirectory(title="Sélectionner un dossier d’images")
        if folder:
            self.folder_var.set(folder)

    def on_generate(self):
        folder = self.folder_var.get().strip()
        if not folder:
            messagebox.showerror("Erreur", "Veuillez sélectionner un dossier d’images.")
            return
        fmt = self.format_var.get()
        try:
            self.progress_var.set("Calcul en cours…")
            self.root.update_idletasks()
            summary = export_trombi(folder, fmt, console_mode=False)
            self.progress_var.set("Terminé.")
            messagebox.showinfo("Succès", summary)
        except Exception as e:
            self.progress_var.set("Erreur.")
            messagebox.showerror("Erreur", str(e))


# =========================
# 9) MAIN (CLI + UI)
# =========================


def main(argv: List[str]) -> int:
    # Usage console: py Trombi_Ecole.py "C:\\Photos\\JY403\\indiv" 42x30
    if len(argv) >= 3:
        folder = argv[1]
        fmt = argv[2]
        try:
            print(export_trombi(folder, fmt, console_mode=True))
            return 0
        except Exception as e:
            print(f"Erreur: {e}")
            return 1

    # Sinon UI
    if tk is None:
        print(
            "Tkinter non disponible. Utilisez: Trombi_Ecole.py <dossier> <42x30|70x50>"
        )
        return 2

    root = tk.Tk()
    App(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
