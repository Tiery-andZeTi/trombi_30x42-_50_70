# Changelog

Du plus récent au plus ancien, en prose, avec le pourquoi.

## 2026-09-16

Deux nouvelles cases à cocher, pensées pour s'articuler avec les dossiers
livrés par NéoTrombino (un sous-dossier par classe, une photo par élève déjà
nommée « Nom Prénom ») :

- **Écrire le nom sous chaque photo.** Décochée par défaut. Le nom du
  fichier (sans son extension) s'incruste sur un bandeau semi-transparent
  collé en bas de chaque vignette — la taille des cellules ne change pas.

  Quand le nom est trop long pour la vignette, le repli se fait en trois
  temps : d'abord on réduit la police ; si ça ne suffit toujours pas, on
  retire le prénom pour ne garder que le nom de famille ; et seulement en
  tout dernier recours, on coupe le texte au nombre de caractères qui
  rentre — **sans points de suspension**. Ce dernier point est volontaire :
  des « … » sur un nom déjà long, souvent un nom d'origine étrangère,
  pouvaient devenir un sobriquet moqueur dans une cour d'école.

- **Ce dossier contient des sous-dossiers de classes.** Décochée par
  défaut. Réunit toutes les photos de tous les sous-dossiers en **un seul
  grand trombi pour l'école entière**, les classes étant prises dans
  l'ordre alphabétique de leur nom de dossier, sans les mélanger entre
  elles. `trombi_keep.txt` continue de fonctionner, mais désormais lu
  dossier de classe par dossier de classe (pour rester compatible avec un
  éventuel futur outil qui générerait ce fichier classe par classe).

Le mode dossier unique, sans rien cocher, n'a pas changé de comportement
(mêmes noms de fichiers de sortie, mêmes messages qu'avant).

Les deux options sont aussi disponibles en ligne de commande, via `--nom`
et `--classes` (voir le README).
