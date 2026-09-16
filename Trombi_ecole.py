import concurrent.futures as cf
import os
import re
import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

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

# Nom incruste sous chaque photo (optionnel, case a cocher dans l'UI)
NAME_BAND_HEIGHT_RATIO = 0.14  # hauteur du bandeau = 14% de la hauteur de la photo
NAME_BAND_ALPHA = 160  # opacite du bandeau noir (0-255)
NAME_FONT_NAME = "arial.ttf"
NAME_MIN_FONT_PX = 10
NAME_TEXT_SIDE_PADDING_RATIO = 0.06

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

# Hauteur de cellule minimale plausible, sous laquelle une vignette n'a plus de sens
CELL_HEIGHT_MIN_PX = 20

# Traitement des photos en parallele (decodage/redimensionnement/cadre)
MAX_WORKERS = max(1, (os.cpu_count() or 1) - 1)

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
    exts = {".jpg", ".jpeg"}
    paths = []
    try:
        for name in os.listdir(folder):
            p = os.path.join(folder, name)
            if os.path.isfile(p) and os.path.splitext(name)[1].lower() in exts:
                paths.append(p)
    except FileNotFoundError:
        return []
    paths.sort(key=natural_sort_key)
    return paths


def read_trombi_keep(folder: str) -> Optional[set]:
    """Lit trombi_keep.txt s'il existe : liste d'inclusion (un nom de fichier par ligne).
    Retourne None si le fichier est absent (aucun filtrage)."""
    keep_path = os.path.join(folder, "trombi_keep.txt")
    if not os.path.isfile(keep_path):
        return None
    with open(keep_path, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def classify_images(paths: List[str]) -> Tuple[List[str], List[str], List[str]]:
    """Un seul passage par fichier : verifie la lisibilite et separe
    portraits / horizontales (orientation EXIF prise en compte).
    Retourne (portraits, horizontales, fichiers illisibles)."""
    portraits: List[str] = []
    landscapes: List[str] = []
    bad: List[str] = []
    for p in paths:
        try:
            with Image.open(p) as im:
                w, h = im.size
                orientation = im.getexif().get(274, 1)
                if orientation in (5, 6, 7, 8):
                    w, h = h, w
                im.verify()  # validation, sans decoder les pixels
            if w > h:
                landscapes.append(p)
            else:
                portraits.append(p)
        except Exception:
            bad.append(os.path.basename(p))
    return portraits, landscapes, bad


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
# 3) ZONE-TITRE & GRILLE UNIQUE
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


def build_grid_rows(
    area: Rect, w_eff_cell: int, h_eff_cell: int, hole: Optional[Rect] = None
) -> List[List[Tuple[int, int]]]:
    """Grille a pas constant sur toute la zone, en sautant les cellules qui
    chevauchent 'hole' (le rectangle du titre). Une seule grille continue,
    pas des zones independantes : les colonnes restent alignees de part et
    d'autre du trou."""
    if area.w <= 0 or area.h <= 0 or w_eff_cell <= 0 or h_eff_cell <= 0:
        return []

    cols = max(0, (area.w + GOUTTIERE_PX) // (w_eff_cell + GOUTTIERE_PX))
    rows = max(0, (area.h + GOUTTIERE_PX) // (h_eff_cell + GOUTTIERE_PX))
    if cols <= 0 or rows <= 0:
        return []

    total_w = cols * w_eff_cell + (cols - 1) * GOUTTIERE_PX
    total_h = rows * h_eff_cell + (rows - 1) * GOUTTIERE_PX
    x0 = area.x0 + max(0, (area.w - total_w) // 2)
    y0 = area.y0 + max(0, (area.h - total_h) // 2)

    grid: List[List[Tuple[int, int]]] = []
    for r in range(rows):
        y = y0 + r * (h_eff_cell + GOUTTIERE_PX)
        row: List[Tuple[int, int]] = []
        for c in range(cols):
            x = x0 + c * (w_eff_cell + GOUTTIERE_PX)
            if hole is not None:
                cell = Rect(x, y, x + w_eff_cell, y + h_eff_cell)
                inter = intersect(cell, hole)
                if inter.w > 0 and inter.h > 0:
                    continue
            row.append((x, y))
        grid.append(row)
    return grid


def place_in_grid_rows(
    grid: List[List[Tuple[int, int]]], count: int, w_eff_cell: int
) -> List[Tuple[int, int]]:
    """Place 'count' photos ligne par ligne. Si la derniere ligne utilisee
    n'est pas remplie, le groupe est centre dans la largeur de la ligne au
    meme pas que les autres, plutot que d'etirer l'espacement entre photos."""
    positions: List[Tuple[int, int]] = []
    placed = 0
    for row in grid:
        if placed >= count:
            break
        if not row:
            continue
        n_in_row = min(len(row), count - placed)
        if n_in_row < len(row):
            row_span = (row[-1][0] + w_eff_cell) - row[0][0]
            used_span = n_in_row * w_eff_cell + (n_in_row - 1) * GOUTTIERE_PX
            base_x = row[0][0] + max(0, (row_span - used_span) // 2)
            y = row[0][1]
            for i in range(n_in_row):
                positions.append((base_x + i * (w_eff_cell + GOUTTIERE_PX), y))
        else:
            positions.extend(row)
        placed += n_in_row
    return positions


# =========================
# 4) DIMENSIONNEMENT (verticales + horizontales groupees)
# =========================


def landscape_content_dims(h_portrait_cell: int) -> Tuple[int, int]:
    """Cellule horizontale a aire egale a la cellule verticale : dimensions
    inversees (largeur <-> hauteur), puisque le ratio horizontal (3:2) est
    exactement l'inverse du ratio vertical (2:3)."""
    w_portrait_cell = int(round(RATIO_VIGNETTE * h_portrait_cell))
    return h_portrait_cell, w_portrait_cell  # (largeur, hauteur) horizontale


def evaluate_layout(W: int, H: int, n_landscape: int, h_p: int) -> dict:
    """Pour une hauteur de cellule verticale h_p donnee : dimensionne le bloc
    d'horizontales (aire egale) en bas, puis calcule la grille unique des
    verticales dans le reste de la zone (trou pour le titre)."""
    title = compute_title_rect(W, H)
    area = Rect(
        MARGE_EXTERIEURE_PX,
        MARGE_EXTERIEURE_PX,
        W - MARGE_EXTERIEURE_PX,
        H - MARGE_EXTERIEURE_PX,
    )

    w_eff_p = int(round(RATIO_VIGNETTE * h_p)) + 2 * CADRE_BORDURE_PX
    h_eff_p = h_p + 2 * CADRE_BORDURE_PX

    if n_landscape > 0:
        w_land, h_land = landscape_content_dims(h_p)
        w_eff_l = w_land + 2 * CADRE_BORDURE_PX
        h_eff_l = h_land + 2 * CADRE_BORDURE_PX
        cols_l = max(1, (area.w + GOUTTIERE_PX) // (w_eff_l + GOUTTIERE_PX))
        rows_l = -(-n_landscape // cols_l)  # ceil
        band_h = rows_l * (h_eff_l + GOUTTIERE_PX) - GOUTTIERE_PX
        vert_area = Rect(area.x0, area.y0, area.x1, area.y1 - band_h - GOUTTIERE_PX)
        band_area = Rect(area.x0, area.y1 - band_h, area.x1, area.y1)
    else:
        w_eff_l = h_eff_l = 0
        vert_area = area
        band_area = Rect(area.x0, area.y1, area.x1, area.y1)

    vert_grid = build_grid_rows(vert_area, w_eff_p, h_eff_p, title)
    land_grid = build_grid_rows(band_area, w_eff_l, h_eff_l, title) if n_landscape > 0 else []

    return {
        "h_p": h_p,
        "w_eff_p": w_eff_p,
        "h_eff_p": h_eff_p,
        "w_eff_l": w_eff_l,
        "h_eff_l": h_eff_l,
        "vert_grid": vert_grid,
        "vert_capacity": sum(len(row) for row in vert_grid),
        "land_grid": land_grid,
        "land_capacity": sum(len(row) for row in land_grid),
    }


def solve_layout(W: int, H: int, n_portrait: int, n_landscape: int) -> Optional[dict]:
    """Cherche la plus grande hauteur de cellule verticale h_p telle que les
    verticales tiennent dans la grille unique, une fois le bloc d'horizontales
    reserve en bas. Recherche binaire : plus h_p est grand, plus les deux
    blocs grossissent et moins il reste de place, donc la capacite verticale
    decroit avec h_p. Retourne None si meme la hauteur minimale ne suffit."""
    area_h = H - 2 * MARGE_EXTERIEURE_PX
    lo, hi = CELL_HEIGHT_MIN_PX, area_h
    best = None
    while lo <= hi:
        mid = (lo + hi) // 2
        result = evaluate_layout(W, H, n_landscape, mid)
        if result["vert_capacity"] >= n_portrait and result["land_capacity"] >= n_landscape:
            best = result
            lo = mid + 1
        else:
            hi = mid - 1
    return best


# =========================
# 5) RENDU VIGNETTE (cadre collé à la photo)
# =========================


def _fit_font(text: str, max_w: int, max_h: int):
    """Plus grande taille d'Arial (entre NAME_MIN_FONT_PX et max_h) qui tient
    dans max_w. Se rabat sur la police par défaut si Arial est introuvable."""
    size = max_h
    smallest_tried = None
    while size >= NAME_MIN_FONT_PX:
        try:
            candidate = ImageFont.truetype(NAME_FONT_NAME, size)
        except Exception:
            return ImageFont.load_default()
        bbox = candidate.getbbox(text)
        if bbox[2] - bbox[0] <= max_w:
            return candidate
        smallest_tried = candidate
        size -= 1
    return smallest_tried or ImageFont.load_default()


def _is_name_upper(token: str) -> bool:
    """Un mot est considere comme le NOM (pas le prenom) s'il est ecrit tout
    en majuscules -- la convention par defaut de NeoTrombino ("[Nom] [Prenom]",
    NOM en MAJUSCULES, Prenom avec une majuscule par partie)."""
    letters = [c for c in token if c.isalpha()]
    return bool(letters) and all(c.isupper() for c in letters)


def _family_name_only(name: str) -> str:
    """Ne garde que les mots tout en majuscules (le NOM), dans leur ordre
    d'origine. Retourne une chaine vide si aucun mot ne s'y prete."""
    return " ".join(t for t in name.split(" ") if _is_name_upper(t))


def _hard_cut(draw: "ImageDraw.ImageDraw", text: str, font, max_w: int) -> str:
    """Coupe le texte au nombre de caracteres qui rentre, SANS points de
    suspension : un nom coupe en "..." peut devenir un sobriquet moqueur,
    surtout pour un nom d'origine etrangere plus long que la moyenne."""
    truncated = text
    while truncated and draw.textbbox((0, 0), truncated, font=font)[2] > max_w:
        truncated = truncated[:-1]
    return truncated


def add_name_band(img: Image.Image, name: str) -> Image.Image:
    """Incruste le nom sur un bandeau semi-transparent collé au bas de la
    photo, sans changer la taille de l'image (la cellule ne bouge pas).

    Si le nom complet ne tient pas, meme en reduisant la police au minimum,
    on enleve d'abord le prenom (on garde le NOM) plutot que de couper le
    texte -- et seulement si meme le nom seul ne tient pas, on coupe au
    nombre de caracteres qui rentre, sans "..."."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    w, h = img.size
    band_h = max(1, int(round(h * NAME_BAND_HEIGHT_RATIO)))
    overlay = Image.new("RGBA", (w, band_h), (0, 0, 0, NAME_BAND_ALPHA))
    img.paste(overlay, (0, h - band_h), overlay)

    pad_x = int(round(w * NAME_TEXT_SIDE_PADDING_RATIO))
    max_text_w = max(1, w - 2 * pad_x)
    max_font_px = max(NAME_MIN_FONT_PX, int(round(band_h * 0.6)))

    draw = ImageDraw.Draw(img)

    display_name = name
    font = _fit_font(display_name, max_text_w, max_font_px)
    if draw.textbbox((0, 0), display_name, font=font)[2] > max_text_w:
        nom_seul = _family_name_only(name)
        if nom_seul and nom_seul != name:
            display_name = nom_seul
            font = _fit_font(display_name, max_text_w, max_font_px)
        if draw.textbbox((0, 0), display_name, font=font)[2] > max_text_w:
            display_name = _hard_cut(draw, display_name, font, max_text_w)

    bbox = draw.textbbox((0, 0), display_name, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (w - tw) / 2 - bbox[0]
    ty = h - band_h + (band_h - th) / 2 - bbox[1]
    draw.text((tx, ty), display_name, fill=(255, 255, 255), font=font)
    return img


def build_block_with_tight_frame(
    img: Image.Image, w_cell: int, h_cell: int, name: Optional[str] = None
) -> Image.Image:
    """
    Crée un bloc (image redimensionnée + cadre noir collé à l'image) sans remplir la cellule 2:3.
    Le bloc peut donc être plus petit que la cellule. On le centrera dans la cellule au collage.
    """
    src = img
    # Convertir si besoin
    if src.mode not in ("RGB", "RGBA"):
        src = src.convert("RGB")

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

    # Nom incruste avant le cadre, pour qu'il reste a l'interieur du contour noir
    if name:
        resized = add_name_band(resized, name)

    # Ajouter cadre noir collé à l'image (autour du contenu)
    block = ImageOps.expand(resized, border=CADRE_BORDURE_PX, fill=CADRE_COULEUR)

    # Le block est en RGB par défaut -> pour collage avec transparence, on convertit en RGBA avec alpha opaque
    if block.mode != "RGBA":
        block = block.convert("RGBA")

    return block


# =========================
# 6) PRÉPARATION EN PARALLÈLE
# =========================


def _prepare_block(
    job: Tuple[str, int, int, Optional[str]]
) -> Tuple[Optional[Image.Image], Optional[str]]:
    """Ouvre une photo, applique draft() puis le redressement EXIF, et
    construit son bloc. draft() doit voir l'image dans son etat JPEG natif :
    appele avant exif_transpose(), il permet a Pillow de decoder directement
    a une resolution proche de la cible au lieu de tout decoder puis reduire."""
    img_path, w_cell, h_cell, name = job
    try:
        with Image.open(img_path) as im:
            try:
                im.draft("RGB", (w_cell, h_cell))
            except Exception:
                pass
            im = ImageOps.exif_transpose(im)
            return build_block_with_tight_frame(im, w_cell, h_cell, name), None
    except Exception as e:
        return None, str(e)


# =========================
# 7) EXPORT PRINCIPAL (streaming low-memory)
# =========================


def _list_and_filter(folder: str) -> Tuple[List[str], int, bool]:
    """Liste les JPG d'un dossier et applique trombi_keep.txt s'il existe.
    Retourne (fichiers gardés, nombre exclus, trombi_keep.txt présent ?)."""
    files = list_images_non_recursive(folder)
    keep_names = read_trombi_keep(folder)
    if keep_names is None:
        return files, 0, False
    before = len(files)
    files = [p for p in files if os.path.basename(p) in keep_names]
    return files, before - len(files), True


def export_trombi(
    folder: str,
    fmt_key: str,
    console_mode: bool = False,
    write_name: bool = False,
    files_override: Optional[List[str]] = None,
    out_name_label: Optional[str] = None,
    extra_header: Optional[str] = None,
) -> str:
    if fmt_key not in FORMATS_PX:
        raise ValueError(f"Format inconnu: {fmt_key}")

    W, H = FORMATS_PX[fmt_key]

    if files_override is not None:
        # Mode "sous-dossiers de classes" : la liste (deja filtree classe par
        # classe par l'appelant) et le resume trombi_keep.txt sont deja prets.
        files_all = files_override
        excluded_by_keep = 0
        keep_present = False
    else:
        files_all, excluded_by_keep, keep_present = _list_and_filter(folder)

    if not files_all:
        raise RuntimeError("Dossier vide ou introuvable.")

    # Classer par lisibilite et orientation (un seul passage par fichier)
    portrait_paths, landscape_paths, bad_files = classify_images(files_all)
    N_portrait = len(portrait_paths)
    N_landscape = len(landscape_paths)
    N = N_portrait + N_landscape
    if N == 0:
        raise RuntimeError("Aucune image lisible dans le dossier.")

    layout = solve_layout(W, H, N_portrait, N_landscape)
    if layout is None:
        max_capacity = evaluate_layout(W, H, N_landscape, CELL_HEIGHT_MIN_PX)["vert_capacity"]
        raise RuntimeError(
            f"{N} photos ne tiennent pas dans le format {fmt_key} "
            f"(capacité maximale à hauteur de cellule minimale : {max_capacity}). "
            "Réduire le nombre de photos ou choisir un format plus grand."
        )

    w_eff_p, h_eff_p = layout["w_eff_p"], layout["h_eff_p"]
    w_eff_l, h_eff_l = layout["w_eff_l"], layout["h_eff_l"]
    w_cell_p, h_cell_p = w_eff_p - 2 * CADRE_BORDURE_PX, h_eff_p - 2 * CADRE_BORDURE_PX
    w_cell_l, h_cell_l = landscape_content_dims(h_cell_p)

    positions_portrait = place_in_grid_rows(layout["vert_grid"], N_portrait, w_eff_p)
    positions_landscape = place_in_grid_rows(layout["land_grid"], N_landscape, w_eff_l)

    # Canevas final (transparent)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # Preparation en parallele (decodage/redimensionnement/cadre), collage
    # sequentiel sur le canevas au fur et a mesure (paste n'est pas thread-safe)
    placed = 0

    def _name_of(path: str) -> Optional[str]:
        return os.path.splitext(os.path.basename(path))[0] if write_name else None

    jobs = (
        [(p, pos, w_cell_p, h_cell_p, w_eff_p, h_eff_p, _name_of(p)) for p, pos in zip(portrait_paths, positions_portrait)]
        + [(p, pos, w_cell_l, h_cell_l, w_eff_l, h_eff_l, _name_of(p)) for p, pos in zip(landscape_paths, positions_landscape)]
    )
    with cf.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_job = {
            executor.submit(_prepare_block, (img_path, w_cell, h_cell, name)): (img_path, cell_pos, w_eff_cell, h_eff_cell)
            for img_path, cell_pos, w_cell, h_cell, w_eff_cell, h_eff_cell, name in jobs
        }
        for future in cf.as_completed(future_to_job):
            img_path, cell_pos, w_eff_cell, h_eff_cell = future_to_job[future]
            block, _error = future.result()
            if block is None:
                bad_files.append(os.path.basename(img_path))
                continue

            # Centrer le bloc dans la cellule (w_eff_cell x h_eff_cell)
            bx, by = block.size
            cx, cy = cell_pos
            x = cx + max(0, (w_eff_cell - bx) // 2)
            y = cy + max(0, (h_eff_cell - by) // 2)

            # Collage: utiliser paste avec masque alpha (économe en RAM)
            canvas.paste(block, (x, y), block)
            placed += 1

    # Export PNG 300 DPI (sans optimize pour la vitesse)
    if out_name_label is not None:
        label = out_name_label
    else:
        label = os.path.basename(os.path.dirname(os.path.abspath(folder))) or "export"
    out_name = f"trombi_{fmt_key}_{label}.png"
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
        f"Verticales: {N_portrait} — cellule {h_cell_p}×{w_cell_p}px (h×w), avec cadre {h_eff_p}×{w_eff_p}px\n"
    )
    if N_landscape > 0:
        summary += (
            f"Horizontales: {N_landscape} (regroupées en fin de trombi) — "
            f"cellule {h_cell_l}×{w_cell_l}px (h×w), avec cadre {h_eff_l}×{w_eff_l}px\n"
        )
    summary += "Bloc moyen ≈ image redimensionnée + cadre (centré dans la cellule)"

    if bad_files:
        summary += "\nFichiers ignorés: " + ", ".join(bad_files[:10])
        if len(bad_files) > 10:
            summary += f" … (+{len(bad_files) - 10})"

    if keep_present:
        summary += f"\ntrombi_keep.txt détecté : {excluded_by_keep} photo(s) exclue(s) (hors liste, ex. ardoises)"

    if extra_header:
        summary = extra_header + "\n\n" + summary

    return summary


def export_trombi_classes(school_folder: str, fmt_key: str, write_name: bool = False) -> str:
    """Regroupe TOUTES les photos de TOUS les sous-dossiers de classes en un
    seul grand trombi pour l'ecole entiere. Les classes sont prises dans
    l'ordre alphabetique de leur nom de sous-dossier, sans les melanger entre
    elles (a l'interieur d'une classe, l'ordre des fichiers est conserve)."""
    try:
        entries = [
            e for e in os.listdir(school_folder)
            if os.path.isdir(os.path.join(school_folder, e))
        ]
    except FileNotFoundError:
        entries = []
    entries.sort(key=natural_sort_key)

    if not entries:
        raise RuntimeError("Aucun sous-dossier de classe trouvé dans ce dossier.")

    combined_files: List[str] = []
    per_class_lines: List[str] = []
    for entry in entries:
        subfolder = os.path.join(school_folder, entry)
        files, excluded, keep_present = _list_and_filter(subfolder)
        combined_files.extend(files)
        line = f"{entry} : {len(files)} photo(s)"
        if keep_present:
            line += f" ({excluded} exclue(s) par trombi_keep.txt)"
        per_class_lines.append(line)

    if not combined_files:
        raise RuntimeError("Aucune photo trouvée dans les sous-dossiers de classes.")

    label = os.path.basename(os.path.normpath(school_folder)) or "export"
    header = (
        f"Classes traitées ({len(entries)}), dans l'ordre alphabétique :\n"
        + "\n".join(f"  - {line}" for line in per_class_lines)
    )

    return export_trombi(
        school_folder,
        fmt_key,
        write_name=write_name,
        files_override=combined_files,
        out_name_label=label,
        extra_header=header,
    )


# =========================
# 8) UI TKINTER (identique, sans alerte <300 px)
# =========================


class App:
    def __init__(self, root):
        self.root = root
        root.title("Trombi École V1.0")
        root.geometry("520x280")

        self.folder_var = tk.StringVar()
        self.format_var = tk.StringVar(value="42x30")
        self.progress_var = tk.StringVar(value="Prêt.")
        self.write_name_var = tk.BooleanVar(value=False)
        self.classes_var = tk.BooleanVar(value=False)

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

        tk.Checkbutton(
            frm,
            text="Écrire le nom (nom du fichier) sous chaque photo",
            variable=self.write_name_var,
        ).grid(row=row, column=0, columnspan=3, sticky="w", pady=(8, 0))
        row += 1

        tk.Checkbutton(
            frm,
            text="Ce dossier contient des sous-dossiers de classes (un seul grand trombi)",
            variable=self.classes_var,
        ).grid(row=row, column=0, columnspan=3, sticky="w")
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
        write_name = self.write_name_var.get()
        classes_mode = self.classes_var.get()
        try:
            self.progress_var.set("Calcul en cours…")
            self.root.update_idletasks()
            if classes_mode:
                summary = export_trombi_classes(folder, fmt, write_name=write_name)
            else:
                summary = export_trombi(folder, fmt, write_name=write_name, console_mode=False)
            self.progress_var.set("Terminé.")
            messagebox.showinfo("Succès", summary)
        except Exception as e:
            self.progress_var.set("Erreur.")
            messagebox.showerror("Erreur", str(e))


# =========================
# 9) MAIN (CLI + UI)
# =========================


def main(argv: List[str]) -> int:
    # Usage console: py Trombi_Ecole.py "C:\\Photos\\JY403\\indiv" 42x30 [--nom] [--classes]
    if len(argv) >= 3:
        folder = argv[1]
        fmt = argv[2]
        flags = set(argv[3:])
        write_name = "--nom" in flags
        classes_mode = "--classes" in flags
        try:
            if classes_mode:
                print(export_trombi_classes(folder, fmt, write_name=write_name))
            else:
                print(export_trombi(folder, fmt, write_name=write_name, console_mode=True))
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
