// database.js
const sqlite3 = require('sqlite3').verbose();

const db = new sqlite3.Database('./users.db', (err) => {
  if (err) console.error('DB open error:', err);
  else console.log('Connected to users.db');
});

db.serialize(() => {
  db.run(
    'CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, name TEXT)',
    (err) => {
      if (err) console.error('Table create error:', err);
    }
  );
});

module.exports = db;
