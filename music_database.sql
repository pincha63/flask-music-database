-- Enable foreign key support
PRAGMA foreign_keys = ON;

-- Create artists table
CREATE TABLE artists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- Create genres table
CREATE TABLE genres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- Create albums table
CREATE TABLE albums (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    artist_id INTEGER NOT NULL,
    FOREIGN KEY (artist_id) REFERENCES artists(id)
);

-- Create songs table
CREATE TABLE songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    duration INTEGER NOT NULL -- in seconds
);

-- Create album_songs junction table for many-to-many relationship between albums and songs
CREATE TABLE album_songs (
    album_id INTEGER NOT NULL,
    song_id INTEGER NOT NULL,
    PRIMARY KEY (album_id, song_id),
    FOREIGN KEY (album_id) REFERENCES albums(id),
    FOREIGN KEY (song_id) REFERENCES songs(id)
);

-- Create song_genres junction table for many-to-many relationship between songs and genres
CREATE TABLE song_genres (
    song_id INTEGER NOT NULL,
    genre_id INTEGER NOT NULL,
    PRIMARY KEY (song_id, genre_id),
    FOREIGN KEY (song_id) REFERENCES songs(id),
    FOREIGN KEY (genre_id) REFERENCES genres(id)
);

-- Create album_genres junction table for many-to-many relationship between albums and genres
CREATE TABLE album_genres (
    album_id INTEGER NOT NULL,
    genre_id INTEGER NOT NULL,
    PRIMARY KEY (album_id, genre_id),
    FOREIGN KEY (album_id) REFERENCES albums(id),
    FOREIGN KEY (genre_id) REFERENCES genres(id)
);

-- Populate artists table
INSERT INTO artists (name) VALUES ('The Beatles'), ('Led Zeppelin'), ('Pink Floyd');

-- Populate genres table
INSERT INTO genres (name) VALUES ('Rock'), ('Psychedelic Rock'), ('Hard Rock'), ('Folk Rock');

-- Populate albums table
INSERT INTO albums (title, artist_id)
VALUES
    ('Abbey Road', 1),
    ('Sgt. Pepper''s Lonely Hearts Club Band', 1),
    ('Led Zeppelin IV', 2),
    ('The Dark Side of the Moon', 3);

-- Populate songs table
INSERT INTO songs (title, duration)
VALUES
    ('Come Together', 260),
    ('Something', 182),
    ('Maxwell''s Silver Hammer', 207),
    ('Oh! Darling', 207),
    ('Octopus''s Garden', 171),
    ('I Want You (She''s So Heavy)', 467),
    ('Here Comes the Sun', 185),
    ('Because', 165),
    ('You Never Give Me Your Money', 242),
    ('Sun King', 146),
    ('Mean Mr. Mustard', 66),
    ('Polythene Pam', 73),
    ('She Came in Through the Bathroom Window', 117),
    ('Golden Slumbers', 91),
    ('Carry That Weight', 96),
    ('The End', 141),
    ('Her Majesty', 23),
    ('Sgt. Pepper''s Lonely Hearts Club Band', 122),
    ('With a Little Help from My Friends', 164),
    ('Lucy in the Sky with Diamonds', 208),
    ('Getting Better', 168),
    ('Fixing a Hole', 156),
    ('She''s Leaving Home', 215),
    ('Being for the Benefit of Mr. Kite!', 157),
    ('Within You Without You', 305),
    ('When I''m Sixty-Four', 157),
    ('Lovely Rita', 162),
    ('Good Morning Good Morning', 161),
    ('Sgt. Pepper''s Lonely Hearts Club Band (Reprise)', 77),
    ('A Day in the Life', 333),
    ('Black Dog', 295),
    ('Rock and Roll', 220),
    ('The Battle of Evermore', 351),
    ('Stairway to Heaven', 482),
    ('Misty Mountain Hop', 278),
    ('Four Sticks', 284),
    ('Going to California', 211),
    ('When the Levee Breaks', 427),
    ('Speak to Me', 90),
    ('Breathe', 163),
    ('On the Run', 210),
    ('Time', 429),
    ('The Great Gig in the Sky', 279),
    ('Money', 382),
    ('Us and Them', 461),
    ('Any Colour You Like', 205),
    ('Brain Damage', 230),
    ('Eclipse', 123);

-- Populate album_songs table
INSERT INTO album_songs (album_id, song_id)
VALUES
    (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10), (1, 11), (1, 12), (1, 13), (1, 14), (1, 15), (1, 16), (1, 17),
    (2, 18), (2, 19), (2, 20), (2, 21), (2, 22), (2, 23), (2, 24), (2, 25), (2, 26), (2, 27), (2, 28), (2, 29), (2, 30),
    (3, 31), (3, 32), (3, 33), (3, 34), (3, 35), (3, 36), (3, 37), (3, 38),
    (4, 39), (4, 40), (4, 41), (4, 42), (4, 43), (4, 44), (4, 45), (4, 46), (4, 47), (4, 48);

-- Populate song_genres table
INSERT INTO song_genres (song_id, genre_id)
VALUES
    (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1), (8, 1), (9, 1), (10, 1), (11, 1), (12, 1), (13, 1), (14, 1), (15, 1), (16, 1), (17, 1),
    (18, 1), (18, 2), (19, 1), (19, 2), (20, 2), (21, 1), (21, 2), (22, 2), (23, 1), (24, 2), (25, 2), (26, 1), (27, 1), (28, 1), (29, 1), (30, 2),
    (31, 3), (32, 1), (33, 4), (34, 3), (34, 4), (35, 3), (36, 3), (37, 4), (38, 3),
    (39, 2), (40, 2), (41, 2), (42, 2), (43, 2), (44, 2), (45, 2), (46, 2), (47, 2), (48, 2);

-- Populate album_genres table
INSERT INTO album_genres (album_id, genre_id)
VALUES
    (1, 1),
    (2, 1), (2, 2),
    (3, 1), (3, 3), (3, 4),
    (4, 2);
