const express = require("express");
const db = require("./db"); // our db.js
const bodyParser = require("body-parser");

const app = express();
app.use(bodyParser.json());

// API to insert user
app.post("/add", (req, res) => {
  const { id, name } = req.body;

  const query = "INSERT INTO users (id, name) VALUES (?, ?)";
  db.query(query, [id, name], (err, result) => {
    if (err) {
      console.error(err);
      return res.status(500).send("Error inserting user");
    }
    res.send("User added successfully ✅");
  });
});

// API to get user by id
app.get("/user/:id", (req, res) => {
  const { id } = req.params;

  const query = "SELECT * FROM users WHERE id = ?";
  db.query(query, [id], (err, result) => {
    if (err) {
      console.error(err);
      return res.status(500).send("Error fetching user");
    }
    res.json(result);
  });
});

app.listen(5000, () => {
  console.log("Server running on http://localhost:5000");
});
