const mysql = require("mysql2");

// create connection
const db = mysql.createConnection({
  host: "localhost",
  user: "root",        // your MySQL username
  password: "h6@CRwCw4E4qX@X", // replace with your MySQL password
  database: "userdb"
});

// connect
db.connect((err) => {
  if (err) {
    console.error("Database connection failed:", err);
    return;
  }
  console.log("Connected to MySQL ✅");
});

module.exports = db;
