-- Обновляем таблицу tournament с новыми полями
ALTER TABLE tournament ADD COLUMN start_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE tournament ADD COLUMN stars INTEGER DEFAULT 1;
ALTER TABLE tournament ADD COLUMN is_test BOOLEAN DEFAULT 0;
ALTER TABLE tournament ADD COLUMN registration_open BOOLEAN DEFAULT 1;
ALTER TABLE tournament ADD COLUMN is_active BOOLEAN DEFAULT 1;
ALTER TABLE tournament ADD COLUMN is_completed BOOLEAN DEFAULT 0;
ALTER TABLE tournament ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE tournament ADD COLUMN created_by INTEGER REFERENCES user(id);

-- Создаем таблицу для участников турнира
CREATE TABLE IF NOT EXISTS tournament_participant (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    card1_id INTEGER,
    card2_id INTEGER,
    card3_id INTEGER,
    card4_id INTEGER,
    registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tournament_id) REFERENCES tournament(id),
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (card1_id) REFERENCES user_card(id),
    FOREIGN KEY (card2_id) REFERENCES user_card(id),
    FOREIGN KEY (card3_id) REFERENCES user_card(id),
    FOREIGN KEY (card4_id) REFERENCES user_card(id),
    UNIQUE (tournament_id, user_id)
);

-- Создаем таблицу для результатов турнира
CREATE TABLE IF NOT EXISTS tournament_result (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id INTEGER NOT NULL,
    card_id INTEGER NOT NULL,
    score FLOAT NOT NULL,
    place INTEGER NOT NULL,
    FOREIGN KEY (tournament_id) REFERENCES tournament(id),
    FOREIGN KEY (card_id) REFERENCES card(id),
    UNIQUE (tournament_id, card_id)
);
