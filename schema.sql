CREATE TABLE IF NOT EXISTS handler_type (
  id INTEGER PRIMARY KEY,
  name VARCHAR(128) UNIQUE
);

CREATE TABLE IF NOT EXISTS global_setting (
  id INTEGER PRIMARY KEY,
  handler_type INTEGER UNIQUE,
  settings TEXT,
  FOREIGN KEY(handler_type) REFERENCES handler_type(id)
);

CREATE TABLE IF NOT EXISTS handler (
  id INTEGER PRIMARY KEY,
  topic VARCHAR(32) UNIQUE,
  handler_type INTEGER,
  settings TEXT,
  FOREIGN KEY(handler_type) REFERENCES handler_type(id)
);

INSERT OR IGNORE INTO handler_type (name) VALUES ('email');

-- Should we keep track of what notifications were send when and by which handler?
