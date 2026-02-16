DROP TABLE IF EXISTS subscribers;
CREATE TABLE subscribers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  channel TEXT,
  marketing_consent INTEGER DEFAULT 0,
  created_at TEXT
);
