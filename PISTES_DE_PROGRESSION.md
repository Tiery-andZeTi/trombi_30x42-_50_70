# Pistes de progression — Trombi 30x42 / 50x70

Relecture faite le **07/08/2026** avec Claude, à la demande de Thierry.
Aucune ligne de code n'a été modifiée : ce fichier est un simple relevé.

## ⚠️ À lire avant d'appliquer quoi que ce soit

Cette relecture porte sur le commit local **`00c3530` (« readme changer »)**, seul
état disponible sur l'ordinateur fixe le 07/08/2026.

**Il existe probablement une version plus récente sur l'autre ordinateur**, avec
des commits jamais poussés sur GitHub (voir l'annexe git en fin de fichier).
Avant de corriger quoi que ce soit, vérifier que les numéros de ligne et le code
cité ci-dessous correspondent encore. Si l'autre machine a une version plus
avancée, **certains points sont peut-être déjà réglés** — comme l'import
`from math import floor`, inutilisé, déjà retiré dans `00c3530`.

Les numéros de ligne renvoient à `Trombi_ecole.py` dans l'état `00c3530`.

## Ce qui est solide — à ne pas jeter

Le cœur géométrique est correct et bien découpé. En particulier :

- La **recherche dichotomique** de la hauteur de cellule (`find_best_cell_height`)
  est valide : la capacité totale est bien monotone décroissante quand `h`
  augmente, donc la dichotomie a le droit de fonctionner.
- Le découpage en 4 zones autour du titre, le `Rect` avec `intersect`, la
  justification de la dernière ligne partielle : propre.
- Le **traitement image par image** (ouvrir → redimensionner → encadrer → coller
  → fermer) évite de faire exploser la RAM sur un canevas 8268×5906.
- Les fonctions de géométrie sont **pures** — donc triviales à tester (voir §9).

Il n'y a aucune raison de réécrire ce programme depuis zéro.

## 🔴 1. Le trombi généré se retrouve dans le trombi suivant

**`Trombi_ecole.py:418`** écrit le PNG de sortie **dans le dossier source**, et
**`Trombi_ecole.py:75`** accepte `.png` comme extension d'entrée.

Conséquence : on génère un trombi, on s'aperçoit qu'une photo manquait, on la
remet, on relance → **le trombi précédent est traité comme un élève.**

Pire, `natural_sort_key` (ligne 65) retient la plus longue séquence de chiffres
du nom. Sur `trombi_42x30_JY403.png`, elle trouve `42` : le trombi vient se
ranger entre les photos 41 et 43, en plein milieu de la classe.

**Piste, et elle est devenue simple :** puisque le périmètre est **JPG en entrée
uniquement** (voir §3), il suffit de **retirer `.png` des extensions acceptées**.
Le PNG n'est produit que par ce script lui-même — plus aucune sortie ne peut être
relue comme une entrée. Une ligne, et le problème disparaît par construction
plutôt que par filtrage.

En complément, écrire la sortie dans un sous-dossier dédié reste plus propre
(le dossier de photos n'est pas pollué), mais ce n'est plus indispensable.

**Pourquoi c'est prioritaire :** le premier passage ne le montre jamais, le
second oui — et relancer après avoir ajouté une photo oubliée est un geste
normal en production.

## 🔴 2. `trombi_keep.txt` — le producteur existe, le lecteur n'a jamais été écrit

Le `README.md` décrit ce fichier sur 6 lignes, avec exemples, et précise qu'il
« peut être généré automatiquement par un autre script ».

**Vérifié : zéro occurrence de `trombi_keep` dans `Trombi_ecole.py`.**

**Mais l'autre script existe, et il a été retrouvé le 07/08/2026 :**
`AutoNBinternet.write_trombi_keep()`
(`D:\Dev\AutoFlux_Projects\AutoNBinternet\AutoNBinternet.py:593`) écrit bien un
`trombi_keep.txt` dans le dossier des individuelles, un nom de fichier par ligne,
extension comprise — exactement le format décrit par le README.

Donc la fonctionnalité n'a pas été perdue : **seul le lecteur manque.** Le
producteur, lui, tourne déjà en production.

### ⚠️ Et il y a un piège : les deux définitions sont inversées

| Source | Ce que le fichier signifie |
|---|---|
| `AutoNBinternet.write_trombi_keep()` | les photos **à inclure** (il parcourt les segments de classe et écrit **tous** leurs fichiers) — d'où le nom, *keep* |
| `README.md` de Trombi_ecole | « liste les photos **à ne pas utiliser** dans le trombi » |

**L'un décrit une liste d'inclusion, l'autre une liste d'exclusion.** Implémenter
le lecteur en suivant le README produirait un trombi contenant **exactement les
photos qu'il fallait écarter**, et écartant toutes les autres.

**Piste :** trancher la sémantique **avant** d'écrire une seule ligne. Le nom du
fichier (`keep`) et le code du producteur disent tous les deux « inclusion » —
c'est très probablement le README qui est faux. Puis implémenter le lecteur, et
corriger le README.

**Pourquoi c'est prioritaire :** aujourd'hui aucun filtrage n'a lieu, alors que le
README affirme le contraire. On peut croire au boulot que des photos sont écartées
alors qu'elles partent au tirage.

## 🟡 3. La liste d'extensions est sensible à la casse

**`Trombi_ecole.py:75`** : la liste est en dur et énumère les deux casses à la
main.

```python
exts = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}
```

Une casse mixte comme `.Jpg` passe donc à la trappe sans un mot.

**Piste :** comparer sur `os.path.splitext(name)[1].lower()`.

> **Pas de TIF ici.** J'avais d'abord classé ce point en 🟠 en supposant qu'il
> fallait aligner les extensions sur TriStation, qui gère les TIF depuis son §13.
> **C'est faux :** périmètre confirmé le 07/08/2026, cet utilitaire ne traitera
> **jamais que du JPG**, et uniquement des **photos individuelles**. Rien à faire
> côté TIF. (Les trombis de groupe, eux, acceptent le TIFF — c'est un autre
> programme, `D:\Dev\TrombiGroupe`.)

## 🟠 4. Deux disparitions silencieuses

**a) Photos avalées par `zip` — `Trombi_ecole.py:394`**

```python
for img_path, cell_pos in zip(readable_paths, all_cell_positions):
```

Si la capacité calculée est inférieure au nombre de photos, `zip` s'arrête sur
la plus courte des deux listes : **les photos en trop disparaissent sans
erreur.** Seul un compteur discret dans le résumé final en témoigne.

**b) PNG entièrement vide — `Trombi_ecole.py:199`**

Si même `h_min = 20` ne suffit pas à faire tenir toutes les photos,
`find_best_cell_height` renvoie des capacités toutes à zéro. Aucune position
n'est calculée, aucune image n'est collée, et **le PNG vide est exporté sans
qu'aucune exception ne soit levée.**

Peu probable en pratique aux formats actuels, mais c'est un échec muet.

**Piste :** dans les deux cas, lever une vraie erreur plutôt que produire un
fichier faux. Un trombi incomplet qui *ressemble* à un trombi complet est plus
dangereux qu'un plantage.

## 🟠 5. Question de conception : la répartition est déséquilibrée

**`Trombi_ecole.py:367-373`** remplit les zones de façon **gloutonne**, dans
l'ordre haut → gauche → droite → bas, en saturant chaque zone avant de passer à
la suivante.

Résultat : haut, gauche et droite tassés au maximum, et la zone du bas avec les
3 photos restantes, centrées.

**Ce n'est pas un bug, c'est un choix** — mais c'est le point qui change le plus
l'allure du tirage final. À discuter avant d'écrire du code : veut-on équilibrer
la charge entre les 4 zones ?

**Tranché le 23/08/2026 : remplacé, pas juste rééquilibré.** Voir la section
« Refonte validée le 23/08/2026 » plus bas — les 4 zones indépendantes
disparaissent au profit d'une grille unique à pas constant.

## 🟡 6. L'optimisation JPEG `draft()` ne se déclenche jamais

**`Trombi_ecole.py:301`**

```python
if hasattr(img, "format") and img.format == "JPEG":
```

**Vérifié empiriquement le 07/08/2026 :** `ImageOps.exif_transpose()`, appelé
juste avant, renvoie une *copie* de l'image dont l'attribut `.format` vaut
`None`. Le test est donc **toujours faux**.

```
format à l'ouverture      : JPEG
format après exif_transpose : None
```

L'accélération du décodage JPEG que le code croit appliquer est du code mort.

**Corrigé le 23/08/2026.** `draft()` est maintenant appelé sur l'image
d'origine dans `_prepare_block()`, **avant** `exif_transpose()` — et le
traitement de chaque photo (décodage, redimensionnement, accentuation, cadre)
tourne en parallèle sur CPU-1 threads (`ThreadPoolExecutor`, même motif que
`photokit.core`), le collage sur le canevas restant séquentiel.

**Mesuré, comparé à la version committée avant la correction** (320 photos
JPEG 6000×4000px, un format d'appareil photo réaliste) :

| Version | Temps |
|---|---|
| Avant (commit `5ace0bf`) | 47,2 s |
| `draft()` corrigé, mono-thread | ~9× plus rapide (mesuré sur un jeu de 150 photos : 22,1 s → 1,9 s) |
| `draft()` + multithread (CPU-1) | **2,2 s (~21× plus rapide)** |

Note technique posée par ce même bug dans `photokit.core` (même cause,
codebase différente) : voir
`D:\Dev\AutoFlux_Projects\photokit_v1.0.0\PISTES_DE_PROGRESSION.md`. Décision
du 23/08/2026 : ne pas relier les deux projets pour autant — Trombi_ecole
reste indépendant (voir la règle « aucune dépendance entre projets » du
`CLAUDE.md` racine).

## 🟡 7. L'interface gèle sans aucun retour

`on_generate` affiche « Calcul en cours… », puis **bloque la boucle Tkinter**
pendant toute la génération : pas de thread, pas de barre de progression.

Sur 700 photos en 50×70, impossible de savoir si le programme travaille ou s'il
est planté.

**Piste :** générer dans un thread et remonter l'avancement, ou au minimum
afficher « photo n / N » via `update_idletasks()`.

**Toujours vrai après le 23/08/2026, mais moins grave.** Le traitement des
photos tourne déjà en parallèle en interne (voir §6) — le gel de l'interface
dure maintenant quelques secondes au lieu de dizaines de secondes sur un
trombi d'école entière. Le fond du problème (aucun retour visuel pendant ce
temps, aucun moyen de distinguer un calcul en cours d'un plantage) reste
entier pour les très gros trombis (formats 50×70, centaines de photos).

## 🟡 8. Code mort et incohérences cosmétiques

- **`Trombi_ecole.py:44`** — `LOW_MEMORY_MODE = True` est défini, commenté
  « (recommandé) »… et **jamais utilisé** nulle part.
- **`Trombi_ecole.py:335`** — le paramètre `console_mode` d'`export_trombi` est
  accepté, transmis depuis les deux appelants, et **jamais lu**.
- **`Trombi_ecole.py:450`** — le titre de la fenêtre annonce « V0.2 », alors que
  l'exécutable et le README parlent de **V05**.
- Les `except Exception:` sans message n'enregistrent **aucune raison** d'échec :
  un fichier atterrit dans `bad_files` sans qu'on sache pourquoi.
- **`Trombi_ecole.py:390`** — le canevas est entièrement transparent, donc rien
  ne distingue visuellement la zone-titre réservée. **Confirmé intentionnel le
  23/08/2026 par Thierry** : le PNG sert de calque Photoshop posé sur un fond
  préparé à l'avance, commun à presque toutes les écoles. Rien à corriger ici,
  juste à documenter dans le README.
- `Trombi_Ecole_V05.exe` (16 Mo) est versionné dans git. Pas dramatique, mais
  chaque nouvelle version ajoutera 16 Mo **définitifs** à l'historique du dépôt.

## 🟡 9. Aucun test

C'est le contraste le plus net avec TriStation aujourd'hui (77 vérifications).

Or toute la géométrie est faite de **fonctions pures** : `compute_title_rect`,
`compute_zones`, `zone_capacity`, `find_best_cell_height`,
`compute_zone_positions`, `natural_sort_key`. Aucune n'ouvre de fichier, aucune
ne dépend de Tkinter. Elles se testent en quelques lignes, sans image.

**Piste :** un `tests/` minimal sur le même modèle que TriStation, qui couvre au
moins : la somme des capacités des 4 zones, la non-régression du tri naturel sur
les noms `0000.jpg` / `0103_ard.jpg`, et le fait qu'on place bien **toutes** les
photos demandées (ce qui attraperait le point §4a).

## Refonte validée le 23/08/2026 — le template « classique »

Discutée avec Thierry via plusieurs maquettes (rendues en rectangles, sans
vraies photos, pour juger uniquement l'espacement). Décidée, pas encore codée.
Répond au §5 (répartition déséquilibrée) et à un défaut non documenté avant
aujourd'hui : les photos horizontales (jusqu'à 20% du total selon les écoles)
cassaient le rythme visuel, forcées dans la même cellule 2:3 que les
verticales.

**Ce que ce template remplace, pour toutes les écoles (pas seulement le
thème dinosaure ci-dessous) — en particulier utile pour les collèges/lycées,
plus sujets aux photos horizontales :**

1. **Grille unique à pas constant**, au lieu de 4 zones indépendantes
   (haut/gauche/droite/bas) centrées chacune de son côté. Une seule grille
   couvre toute la zone imprimable, en sautant les cellules qui chevauchent
   le rectangle du titre. Élimine l'écart irrégulier entre zones et
   l'absence d'alignement des colonnes de part et d'autre du titre.
2. **Dernière ligne partielle centrée, jamais étirée.** Le pas entre photos
   reste identique à toutes les lignes ; s'il manque des photos pour remplir
   la dernière ligne, l'espace en trop va à gauche/droite du groupe, pas
   entre les photos.
3. **Photos horizontales détectées et regroupées en fin de trombi**, sur un
   ou plusieurs rangs dédiés après toutes les verticales (ordre numérique
   conservé à l'intérieur de chaque groupe). Dimensionnées à **aire égale**
   avec les cellules verticales (dimensions inversées : largeur horizontale
   = hauteur verticale, hauteur horizontale = largeur verticale) — testé
   contre l'option « même hauteur de rangée », écartée car elle grossit
   artificiellement les horizontales (~2,25× la surface) et leur donne une
   importance visuelle non voulue.

**Pas encore réglé avant de coder :** le point §6 (optimisation JPEG `draft()`
morte) et l'absence de multithread restent des sujets séparés, discutés le
même jour mais pas résolus — voir le fil de discussion, pas encore de piste
écrite ici.

## Idées notées le 23/08/2026, écartées pour cette session

Discutées avec Thierry, volontairement pas traitées maintenant.

### La zone-titre pourrait devenir un cercle plutôt qu'un rectangle

L'an dernier, rectangle vide au centre. Cette année, ce pourrait être un
cercle vide. **Idée pour une saison future, pas pour maintenant** — non
tranché. À noter : ce n'est pas qu'un changement cosmétique, la zone-titre
sert aussi à calculer les 4 zones (`compute_zones`) en excluant son
rectangle englobant ; un cercle changerait la géométrie d'exclusion, pas
seulement le rendu.

### Exclure aussi les photos frère/sœur via `multivisage.json`

AutoIndiv écrit (ou écrira) un `multivisage.json` qui pourrait servir, en
plus de `trombi_keep.txt`, à exclure automatiquement les photos où plusieurs
visages sont détectés (fratries). **Idée pour plus tard**, pas cadrée, pas de
format ni d'emplacement de fichier discutés.

### Un second template « thème » : le dinosaure qui prend la fuite

Thème de la saison 2026 pour une école en particulier : le dinosaure (image
de fond) entouré par les photos des élèves, mais avec une **voie de sortie**
pour lui — l'idée visuelle est que la « force collective » des enfants le
fait fuir, sans l'encercler complètement. Une maquette d'encerclement complet
(anneau simple vs plusieurs anneaux concentriques) a été testée le 23/08/2026
pour vérifier la faisabilité géométrique — un anneau (ou plusieurs, répartis
proportionnellement à leur circonférence) autour d'un trou elliptique, calculé
par points à intervalle d'arc égal (pas par angle égal, qui chevauche les
vignettes sur une ellipse). **Mais ce n'est pas la mise en page voulue** :
Thierry fournira sa propre maquette de la scène avec la voie de sortie quand
ce template sera à l'ordre du jour. Traité comme un **second template**,
distinct du « classique » — voir la conclusion du 23/08/2026 plus bas.

## Ordre d'attaque recommandé

**Avant la saison** — moins d'une heure :

1. Le §1 (trombi réinjecté dans le trombi) — retirer `.png` de l'entrée
2. Le §2 (`trombi_keep.txt` : implémenter ou retirer du README)
3. Le §3 (extensions en minuscules) — deux lignes, à faire dans la même passe
   que le §1 puisque ça touche exactement le même endroit

Ces trois-là sécurisent la production. Le §4 mérite d'être fait dans la même
passe si le temps le permet.

**Hors saison** — le reste. Le §5 (équilibrage des zones) demande une décision
esthétique avant tout code, pas l'inverse.

## Annexe — situation git au 07/08/2026

Sans lien avec le code, mais à ne pas perdre de vue.

Le dépôt local et GitHub avaient **divergé** :

```
                    ┌── 288ec6e ── 00c3530  ← ordi fixe, jamais poussé
                    │   « ajout venv »   « readme changer »
  ac71129 ──────────┤
  (dernier état     │
   commun)          └── bf3bfbb  ← GitHub, jamais récupéré ici
                        « Update .gitignore »
```

`git status` annonçait `ahead 2` seulement parce que la copie locale de l'état
GitHub était périmée. Après un `git fetch` (sans effet sur les fichiers), la
vraie situation est apparue : **`ahead 2, behind 1`**.

**Le conflit est faux.** Les deux côtés ont modifié `.gitignore` avec la même
intention :

| Côté | Lignes ajoutées |
|---|---|
| Ordi fixe (local) | `.venv/`, `venv/`, `.env` |
| GitHub | `.venv/` |

La version locale **contient déjà tout** ce que fait la version GitHub. Aucun
travail à sauver côté distant, aucun arbitrage réel. Git signale malgré tout un
conflit, parce qu'il ne peut pas deviner que les deux ajouts visent la même chose.

Les deux autres modifications locales n'entrent en conflit avec rien : dans
`Trombi_ecole.py`, uniquement du rangement d'imports (dont la suppression du
`floor` inutilisé) sans aucune logique touchée ; dans `README.md`, « Pillow,
Tkinter » → « Pillow » et un « A bientôt. » final.

**Origine probable :** les messages `Create README.md`, `Update README.md`,
`Add files via upload`, `Update .gitignore` sont les **messages par défaut de
l'éditeur web de GitHub**. Tout le début du dépôt a donc été fait dans le
navigateur, et seuls les 2 derniers commits avec du vrai git. D'où la divergence.

**Résolution reportée volontairement**, le temps de vérifier l'autre
ordinateur : il peut lui aussi porter des commits jamais poussés, voire une
version plus récente du script. Résoudre ici d'abord ferait courir le risque de
retrouver la même divergence là-bas.

Quand les trois états seront connus, la réparation est simple : rejouer les 2
commits locaux par-dessus celui de GitHub (`git pull --rebase`), résoudre le
faux conflit en gardant la version locale de `.gitignore` — qui est un
sur-ensemble — puis pousser.
