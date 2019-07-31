BEGIN;

CREATE TABLE citizen_info(
    town text NOT NULL,
    street text NOT NULL,
    building text NOT NULL,
    apartment integer NOT NULL,
    citizen_name text NOT NULL,
    birth_date text NOT NULL,
    gender VARCHAR(6) CHECK (gender in ('male', 'female')),
    citizen_id INTEGER NOT NULL,
    import_id SERIAL NOT NULL,
    PRIMARY KEY (citizen_id, import_id)
);

CREATE TABLE citizen_relation(
    citizen_id INTEGER NOT NULL,
    import_id INTEGER NOT NULL,
    relation_id INTEGER NOT NULL,
    FOREIGN KEY (import_id, citizen_id) REFERENCES citizen_info(import_id, citizen_id),
    FOREIGN KEY (import_id, relation_id) REFERENCES citizen_info(import_id, citizen_id)
);


CREATE OR REPLACE FUNCTION insert_import_data_to_citizen_info(
    town text[],
    street text[],
    building text[],
    apartment integer[],
    citizen_name text[],
    birth_date text[],
    gender text[],
    citizen_id integer[]
    ) RETURNS integer AS $$
<< outerblock >>
DECLARE
    last_import_id integer := (SELECT nextval('citizen_info_import_id_seq'));
BEGIN
    INSERT INTO citizen_info(
        town, street, building, apartment, citizen_name,
        birth_date, gender, citizen_id, import_id)
    SELECT 
    unnest(town), unnest(street), unnest(building), unnest(apartment), unnest(citizen_name),
    unnest(birth_date), unnest(gender), unnest(citizen_id), last_import_id;
    
    RETURN last_import_id;
END;
$$ LANGUAGE plpgsql;


COMMIT;
 /*
ТЕСТОВЫЕ ЗАПРОСЫ

 SELECT insert_import_data_to_citizen_info('{Пермь}', '{Ул. Борчанинова}', '{д.6}', '{квартира 61}', '{Алексей Никитин}',
 '{18.06.1997}', '{male}', '{17}'
 );
 

INSERT INTO citizen_info (town,
street, building, apartment, citizen_name, birth_date, gender, citizen_id, import_id)
VALUES ('Москва', 'Пушкина', 'Колотушкина', '1', 'Иванов', '11.1.2019', 'male', 1, 1);


INSERT INTO citizen_relation (relation_id, citizen_id, import_id) VALUES (1,1,1);
*/

