-- Скрипт для удаления карточки и всех связанных записей
-- Заменить ID на фактический ID карточки, которую нужно удалить
BEGIN TRANSACTION;

-- Удаляем записи из таблицы user_card, которые ссылаются на карточку
DELETE FROM user_card WHERE card_id = ID_КАРТОЧКИ;

-- Проверяем, есть ли карточка в командах пользователей
UPDATE team SET slot1_card_id = NULL WHERE slot1_card_id IN (SELECT id FROM user_card WHERE card_id = ID_КАРТОЧКИ);
UPDATE team SET slot2_card_id = NULL WHERE slot2_card_id IN (SELECT id FROM user_card WHERE card_id = ID_КАРТОЧКИ);
UPDATE team SET slot3_card_id = NULL WHERE slot3_card_id IN (SELECT id FROM user_card WHERE card_id = ID_КАРТОЧКИ);
UPDATE team SET slot4_card_id = NULL WHERE slot4_card_id IN (SELECT id FROM user_card WHERE card_id = ID_КАРТОЧКИ);
UPDATE team SET slot5_card_id = NULL WHERE slot5_card_id IN (SELECT id FROM user_card WHERE card_id = ID_КАРТОЧКИ);

-- Удаляем саму карточку
DELETE FROM card WHERE id = ID_КАРТОЧКИ;

COMMIT;
