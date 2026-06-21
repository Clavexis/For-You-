CREATE TABLE users (id INT, name TEXT, age INT);
INSERT INTO users VALUES (1, 'alice', 30);
INSERT INTO users VALUES (2, 'bob', 25);
INSERT INTO users VALUES (3, 'carol', 42);
SELECT * FROM users;
SELECT * FROM users WHERE age > 28;
SELECT * FROM users WHERE id = 2;
DELETE FROM users WHERE name = 'bob';
SELECT * FROM users;
