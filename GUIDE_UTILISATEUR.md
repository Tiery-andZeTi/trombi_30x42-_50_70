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

4. Deux cases à cocher, toutes deux facultatives :

   - **« Écrire le nom (nom du fichier) sous chaque photo »** : incruste le
     nom du fichier (sans son extension) sur chaque vignette. Ne cochez ceci
     que si vos photos sont déjà nommées « Nom Prénom » — c'est ce que fait
     NéoTrombino par défaut à l'export vers l'établissement.
   - **« Ce dossier contient des sous-dossiers de classes »** : à cocher
     quand le dossier choisi à l'étape 2 est le dossier de l'école, avec un
     sous-dossier par classe à l'intérieur (exactement ce que produit
     NéoTrombino). Le programme fabrique alors **un seul et même grand
     trombi** avec toutes les classes, prises dans l'**ordre alphabétique**
     de leur nom de dossier, sans les mélanger entre elles.

5. Cliquez sur **Générer**.

6. Une fenêtre **Succès** apparaît avec un résumé (nombre de photos placées,
   taille des vignettes, et le détail classe par classe si la case
   « sous-dossiers de classes » était cochée). Le fichier PNG a été créé
   **dans le dossier choisi à l'étape 2**, sous un nom du type
   `trombi_42x30_NomDuDossier.png`.



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
- **« Aucun sous-dossier de classe trouvé dans ce dossier »** : la case
  « sous-dossiers de classes » est cochée, mais le dossier choisi contient
  directement des photos et non des sous-dossiers — décochez la case, ou
  choisissez le dossier parent (celui qui contient les dossiers de classe).
- **« Aucune photo trouvée dans les sous-dossiers de classes »** : les
  sous-dossiers existent mais sont vides, ou `trombi_keep.txt` a tout écarté
  dans chacun d'eux.

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
- En mode « sous-dossiers de classes », un `trombi_keep.txt` s'applique à
  l'intérieur du dossier de classe où il se trouve — il n'écarte que les
  photos de cette classe-là, pas celles des autres.
- Le nom écrit sur chaque photo est exactement le nom du fichier, sans
  l'extension. S'il est trop long pour tenir sur une vignette : d'abord il
  est affiché en plus petit ; si ça ne suffit toujours pas, le prénom est
  retiré pour ne garder que le NOM ; et si même le nom seul ne tient pas, il
  est coupé au nombre de caractères qui rentre, **sans points de
  suspension** (volontairement — trois petits points sur un nom déjà long,
  souvent un nom d'origine étrangère, ça peut vite devenir un sobriquet
  moqueur dans une cour d'école).
