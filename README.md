# Trombi 30x42 / 50x70

Ce programme permet de créer automatiquement des trombinoscopes au format 30x42 cm ou 50x70 cm, avec un rectangle vide en haut pour écrire le titre.  
L’application dispose d’une interface graphique réalisée avec Tkinter, en Python.

> Pour une utilisation simple de l'exécutable (sans rien installer), voir le
> [Guide d'utilisation](GUIDE_UTILISATEUR.md).

## Fonctionnalités

- Génération de trombinoscopes en 30x42 cm ou 50x70 cm.
- Interface graphique simple pour choisir les dossiers et options.
- Case à cocher pour incruster le nom (nom du fichier, sans l'extension) sous
  chaque vignette — pensée pour des photos déjà nommées « Nom Prénom »,
  comme celles produites par NéoTrombino.
- Case à cocher pour traiter un dossier contenant un sous-dossier par classe
  (structure produite par NéoTrombino) : toutes les classes sont alors
  fusionnées en **un seul grand trombi**, dans l'ordre alphabétique des noms
  de sous-dossiers, sans les mélanger entre elles.
- Possibilité d’ignorer certaines photos indésirables via le fichier `trombi_keep.txt`.
- Photos d’entrée acceptées : JPG uniquement (le PNG est réservé à la sortie).
- Photos horizontales détectées automatiquement et regroupées sur leur(s) propre(s) rang(s) en fin de trombi, pour ne pas casser le rythme visuel de la grille.
- Décodage optimisé (`draft()`) et traitement des photos en parallèle (CPU-1 threads) : un trombi d'école entière se génère en quelques secondes.

## Installation et prérequis (version Python)

- Installer Python (version 3.10 ou supérieure).
- Installer les bibliothèques nécessaires : Pillow.
- Télécharger les fichiers du dépôt sur votre ordinateur.

Pour lancer le programme :

python Trombi_ecole.py

En ligne de commande (sans interface), deux options facultatives s'ajoutent
après le format :

python Trombi_ecole.py "C:\Photos\Ecole" 42x30 --nom --classes

- `--nom` : incruste le nom du fichier sous chaque photo.
- `--classes` : traite le dossier passé en argument comme un dossier
  d'école contenant un sous-dossier par classe, et fabrique un seul grand
  trombi fusionné.


## Utilisation pas à pas

1. Lancer le programme (ou double-cliquer sur `Trombi_Ecole_V1.0.exe` sous Windows).
2. Choisir le dossier contenant les photos des élèves (ou, si la case
   « sous-dossiers de classes » est cochée, le dossier de l'école contenant
   un sous-dossier par classe).
3. Choisir le format du trombinoscope dans le menu déroulant : `42x30` (30x42 cm) ou `70x50` (50x70 cm).
4. Cocher, si besoin, « Écrire le nom sous chaque photo » et/ou « Ce dossier
   contient des sous-dossiers de classes ».
5. Générer le trombinoscope et vérifier le résultat dans le dossier de sortie.

> Note : le menu déroulant affiche les formats en pixels dans l'ordre largeur × hauteur
> (`42x30`, `70x50`), alors que le nom du produit se lit habituellement en hauteur × largeur
> (30x42 cm, 50x70 cm). Les deux désignent le même format — voir le
> [Guide d'utilisation](GUIDE_UTILISATEUR.md) pour la correspondance.

## Fichiers importants

- `Trombi_ecole.py` : script Python principal.
- `Trombi_Ecole_V1.0.spec` : recette de build PyInstaller (voir plus bas).
- `icone trombi indiv.png` / `icone_trombi_indiv.ico` : source et export de l'icône de l'exécutable.
- `dist/Trombi_Ecole_V1.0.exe` : exécutable Windows, généré par le build (non versionné, voir plus bas).
- `GUIDE_UTILISATEUR.md` : notice destinée à quelqu'un qui utilise seulement l'exécutable, sans toucher au code.
- `trombi_keep.txt` (optionnel, dans le dossier de photos) : liste les photos à **inclure** dans le trombi, une par ligne, avec le nom exact du fichier et son extension. Sert notamment à exclure automatiquement les ardoises. Si le fichier est absent, toutes les photos du dossier sont utilisées.  
  Exemple :
  - `0001.jpg`
  - `0005.JPG`

  En mode « sous-dossiers de classes », le fichier est cherché **dans chaque
  dossier de classe séparément** : il n'écarte que les photos de cette
  classe-là.

> Remarque : ce fichier est généré automatiquement par AutoIndiv, pour le
> dossier envoyé au labo. Le dossier « sortie école » produit par NéoTrombino
> ne passe pas par AutoIndiv et n'en a donc pas aujourd'hui.

## Fabriquer l'exécutable (PyInstaller)

L'exécutable n'est pas versionné dans le dépôt (un binaire compilé n'a pas sa place dans
l'historique Git — voir `.gitignore`, `dist/` est ignoré). Pour le refabriquer :

pip install pyinstaller
pyinstaller Trombi_Ecole_V1.0.spec

Le résultat apparaît dans `dist/Trombi_Ecole_V1.0.exe`. Le `.spec` contient déjà l'icône et
les options utilisées (un seul fichier, sans console).

## État actuel du projet

Ce projet est en cours d’amélioration.  
Il peut encore contenir des bugs ou des comportements non finalisés.  
Toutes remarques ou suggestions sont les bienvenues.
A bientôt.
