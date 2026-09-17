/** Zero-dependency CyberSnake server: Node.js owns the SQLite access. */
import { createServer } from 'node:http';
import { readFileSync, existsSync, mkdirSync } from 'node:fs';
import { extname, join, normalize, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { DatabaseSync } from 'node:sqlite';

const root = resolve(fileURLToPath(new URL('.', import.meta.url)));
const dataDirectory = join(root, 'data');
const databasePath = join(dataDirectory, 'cybersnake.db');
const mimeTypes = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8' };

export function initialiseDatabase() {
  mkdirSync(dataDirectory, { recursive: true });
  const database = new DatabaseSync(databasePath);
  database.exec(readFileSync(join(dataDirectory, 'schema.sql'), 'utf8'));
  const { count } = database.prepare('SELECT COUNT(*) AS count FROM questions').get();
  if (count === 0) database.exec(readFileSync(join(dataDirectory, 'seed.sql'), 'utf8'));
  return database;
}

export function questionsForGame(database, requestedLimit = 10) {
  const { count } = database.prepare('SELECT COUNT(*) AS count FROM questions').get();
  const limit = Math.max(1, Math.min(Number.parseInt(requestedLimit, 10) || 10, count));
  const questionRows = database.prepare('SELECT id, topic, question_text FROM questions ORDER BY RANDOM() LIMIT ?').all(limit);
  const answerStatement = database.prepare('SELECT id, answer_text FROM answer_choices WHERE question_id = ? ORDER BY position');
  return questionRows.map((row) => ({
    id: row.id,
    topic: row.topic,
    question: row.question_text,
    answers: answerStatement.all(row.id).map((answer) => ({ id: answer.id, text: answer.answer_text })),
  }));
}

export function validateAnswer(database, questionId, answerId) {
  const selected = database.prepare('SELECT is_correct FROM answer_choices WHERE id = ? AND question_id = ?').get(answerId, questionId);
  const correct = database.prepare('SELECT id FROM answer_choices WHERE question_id = ? AND is_correct = 1').get(questionId);
  if (!selected || !correct) return null;
  return { is_correct: Boolean(selected.is_correct), correct_answer_id: correct.id };
}

function sendJson(response, statusCode, payload) {
  response.writeHead(statusCode, { 'Content-Type': 'application/json; charset=utf-8' });
  response.end(JSON.stringify(payload));
}

function serveStatic(request, response, pathname) {
  const requestedPath = pathname === '/' ? '/index.html' : pathname;
  const filename = resolve(root, `.${normalize(requestedPath)}`);
  if (!filename.startsWith(root) || !existsSync(filename)) {
    response.writeHead(404); response.end('Page introuvable.'); return;
  }
  response.writeHead(200, { 'Content-Type': mimeTypes[extname(filename)] || 'application/octet-stream' });
  response.end(readFileSync(filename));
}

export function createApp(database) {
  return createServer(async (request, response) => {
    const url = new URL(request.url, 'http://localhost');
    if (request.method === 'GET' && url.pathname === '/api/questions') {
      sendJson(response, 200, { questions: questionsForGame(database, url.searchParams.get('limit')) }); return;
    }
    if (request.method === 'POST' && url.pathname === '/api/answers') {
      let body = '';
      for await (const chunk of request) body += chunk;
      try {
        const { question_id, answer_id } = JSON.parse(body);
        const result = validateAnswer(database, Number(question_id), Number(answer_id));
        if (!result) { sendJson(response, 404, { error: 'Question ou réponse introuvable.' }); return; }
        sendJson(response, 200, result);
      } catch { sendJson(response, 400, { error: 'Réponse invalide.' }); }
      return;
    }
    serveStatic(request, response, url.pathname);
  });
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const database = initialiseDatabase();
  const server = createApp(database);
  server.listen(8000, '127.0.0.1', () => console.log('CyberSnake disponible sur http://127.0.0.1:8000'));
}
