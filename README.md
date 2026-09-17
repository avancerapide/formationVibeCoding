# CyberSnake

Jeu du serpent de validation des connaissances, alimenté par une banque de questions SQLite et une API JavaScript.

## Lancer l’application

Aucune dépendance npm n’est nécessaire : Node.js 24+ fournit directement le module `node:sqlite` utilisé par le serveur JavaScript.

```bash
node server.mjs
```

Ouvrez ensuite <http://127.0.0.1:8000>. Au premier démarrage, le serveur JavaScript crée `data/cybersnake.db` et l’initialise avec les questions et réponses versionnées dans `data/seed.sql`.

## Données et API

- `data/schema.sql` définit les tables relationnelles `questions` et `answer_choices`.
- `data/seed.sql` contient les 40 questions et leurs trois réponses ; la bonne réponse est marquée dans la base avec `is_correct`.
- `server.mjs` accède à SQLite via le module JavaScript natif `node:sqlite`.
- `GET /api/questions?limit=10` sélectionne aléatoirement les questions pour une partie sans exposer les réponses correctes.
- `POST /api/answers` valide une réponse côté serveur avec un corps JSON contenant `question_id` et `answer_id`.
