<img title="" src="file:///D:/Dev/trombi_30x42-_50_70/icone%20trombi%20indiv.png" alt="icone trombi indiv.png" data-align="center" width="193">

# Guide d'utilisation — Trombi École

Ce programme fabrique automatiquement une planche avec toutes les photos
individuelles d'une école, rangées en grille. Le résultat est un fichier PNG
transparent, à poser en calque sur un fond déjà préparé (dans Photoshop par
exemple), avec le nom de l'école ajouté au centre.

Aucune installation n'est nécessaire : il suffit d'avoir le fichier
`Trombi_Ecole_V1.0.exe`.

## Avant de commencer

- Le dossier de photos ne doit contenir que les photos JPG des élèves — pas
  d'autre image dedans.
- S'il y a un fichier `trombi_keep.txt` dans ce dossier, il est pris en
  compte automatiquement (il écarte les ardoises). Rien à faire de votre côté.

## Étape par étape

1. Double-cliquez sur `Trombi_Ecole_V1.0.exe`.

2. Cliquez sur **Parcourir…** et choisissez le dossier contenant les photos
   de l'école.

3. Dans **Format**, choisissez :
   
   - **`42x30`** pour une planche 30x42 cm
   - **`70x50`** pour une planche 50x70 cm
   
   (Le menu affiche les formats en largeur × hauteur ; le nom commercial se
   lit en hauteur × largeur — c'est le même format dans les deux cas.)

4. Cliquez sur **Générer**.

5. Une fenêtre **Succès** apparaît avec un résumé (nombre de photos placées,
   taille des vignettes...). Le fichier PNG a été créé **dans le même
   dossier que les photos**, sous un nom du type `trombi_42x30_NomDuDossier.png`.



___________________________________________________________________________________



## Si une fenêtre d'erreur apparaît

Ce n'est pas un plantage : le programme s'arrête proprement et explique la
raison en clair. Les cas les plus courants :

- **« Veuillez sélectionner un dossier d’images »** : cliquez sur Parcourir
  et choisissez le bon dossier.
- **« ... photos ne tiennent pas dans le format ... »** : il y a trop de
  photos pour le format choisi. Le message indique combien peuvent tenir au
  maximum — essayez l'autre format, ou vérifiez qu'il n'y a pas de photos en
  double dans le dossier.
- **« Dossier vide ou introuvable »** : le dossier ne contient aucune photo
  JPG reconnue.
- **« Aucune image lisible dans le dossier »** : les photos JPG trouvées
  sont illisibles (fichiers corrompus), ou `trombi_keep.txt` les a toutes
  écartées.

## Bon à savoir

- Le calcul est nettement plus rapide qu'avec les anciennes versions du
  programme, même sur un ordinateur avec moins de cœurs que celui utilisé
  pour le développer.
- Les photos prises à l'horizontale sont repérées automatiquement et
  regroupées à la fin de la planche, pour ne pas casser l'alignement des
  autres photos.
- Relancer le programme sur un dossier où un trombi a déjà été généré ne
  pose aucun problème : le PNG déjà créé n'est jamais repris comme une photo
  d'élève.
