# CyberSnake

Jeu du serpent autonome de validation des connaissances.

## Lancer l’application

Ouvrez simplement `index.html` dans un navigateur récent : aucune installation, aucun serveur, aucune dépendance et aucun accès réseau ne sont nécessaires.

## Données locales

La banque de 40 questions et de leurs réponses est incluse dans le JavaScript de `index.html`. À la première partie, elle est copiée dans le `localStorage` du navigateur sous la clé `cybersnake.question-bank.v1`. Les sessions suivantes utilisent cette copie locale, même hors ligne.
