# Trombi 30x42 / 50x70

Ce programme permet de créer automatiquement des trombinoscopes au format 30x42 cm ou 50x70 cm, avec un rectangle vide en haut pour écrire le titre.  
L’application dispose d’une interface graphique réalisée avec Tkinter, en Python.

## Fonctionnalités

- Génération de trombinoscopes en 30x42 cm ou 50x70 cm.
- Interface graphique simple pour choisir les dossiers et options.
- Possibilité d’ignorer certaines photos indésirables via le fichier `trombi_keep.txt`.

## Installation et prérequis (version Python)

- Installer Python (version 3.10 ou supérieure).
- Installer les bibliothèques nécessaires : Pillow, Tkinter.
- Télécharger les fichiers du dépôt sur votre ordinateur.

Pour lancer le programme :

python Trombi_ecole.py


## Utilisation pas à pas

1. Lancer le programme (ou double-cliquer sur `Trombi_Ecole_V05.exe` sous Windows).
2. Choisir le dossier contenant les photos des élèves.
3. Choisir le format du trombinoscope (30x42 ou 50x70).
4. Générer le trombinoscope et vérifier le résultat dans le dossier de sortie.

## Fichiers importants

- `Trombi_ecole.py` : script Python principal.
- `Trombi_Ecole_V05.exe` : version exécutable pour Windows.
- `trombi_keep.txt` : liste les photos à ne pas utiliser dans le trombi, une par ligne, avec le nom exact du fichier et son extension.  
  Exemple :
  - `0000.jpg`
  - `0005.JPG`
  - `0011.png`

> Remarque : ce fichier peut être généré automatiquement par un autre script.

## État actuel du projet

Ce projet est en cours d’amélioration.  
Il peut encore contenir des bugs ou des comportements non finalisés.  
Toutes remarques ou suggestions sont les bienvenues.


