PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS questions (
  id INTEGER PRIMARY KEY,
  topic TEXT NOT NULL,
  question_text TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS answer_choices (
  id INTEGER PRIMARY KEY,
  question_id INTEGER NOT NULL,
  answer_text TEXT NOT NULL,
  is_correct INTEGER NOT NULL CHECK (is_correct IN (0, 1)),
  position INTEGER NOT NULL CHECK (position BETWEEN 1 AND 3),
  FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
  UNIQUE (question_id, position)
);
