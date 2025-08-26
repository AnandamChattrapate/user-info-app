// server.js
const express = require('express');
const path = require('path');
const db = require('./database');

const app = express();

// parse JSON and form data
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Serve static files (add.html, search.html) from project root
app.use(express.static(path.join(__dirname)));

// POST /add  -> add user
app.post('/add', (req, res) => {
  const { id, name } = req.body;
  if (!id || !name) return res.status(400).json({ error: 'id and name required' });

  db.run('INSERT INTO users(id, name) VALUES(?, ?)', [id, name], function (err) {
    if (err) {
      // primary key (duplicate) check
      if (err.message && err.message.includes('SQLITE_CONSTRAINT')) {
        return res.status(400).json({ error: 'User already exists' });
      }
      console.error('DB insert error:', err);
      return res.status(500).json({ error: 'Database error' });
    }
    console.log(`Added user ${id} -> ${name}`);
    res.json({ message: 'User saved!' });
  });
});

// GET /get/:id -> get user name
app.get('/get/:id', (req, res) => {
  const id = req.params.id;
  db.get('SELECT name FROM users WHERE id = ?', [id], (err, row) => {
    if (err) {
      console.error('DB select error:', err);
      return res.status(500).json({ error: 'Database error' });
    }
    if (row) return res.json({ name: row.name });
    return res.status(404).json({ error: 'User not found' });
  });
});

// optional: root -> redirect to add.html
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'add.html'));
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`✅ Server running on http://localhost:${PORT}`));
