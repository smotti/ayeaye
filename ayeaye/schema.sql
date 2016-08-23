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
  handler_type INTEGER,
  topic VARCHAR(32) UNIQUE,
  settings TEXT,
  FOREIGN KEY(handler_type) REFERENCES handler_type(id)
);

CREATE TABLE IF NOT EXISTS notification_archive (
  id INTEGER PRIMARY KEY,
  time INTEGER,
  send_failed BOOLEAN,
  topic VARCHAR(32),
  title VARCHAR(1024),
  content TEXT
);

INSERT OR IGNORE INTO handler_type (name) VALUES ('email');

-- Should we keep track of what notifications were send when and by which handler?
