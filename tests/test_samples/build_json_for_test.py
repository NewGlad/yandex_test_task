import json
import pickle
import random
import os
import datetime
import numpy as np


def get_random_date():
    return datetime.date(random.randint(1960,2019), random.randint(1,12),random.randint(1,28)).strftime("%d.%m.%Y")

def generate_citizens_list(json_size: int):
    '''
        Собирает JSON для тестов требуемого размера
        Данные валидны, но неадвекватны:
            1. адреса получаются ненастоящие,
            2. имя/фамилия/пол генерируются независимо, и, следовательно, не сочетаются между собой
    '''
    citizens_list = []
    for citizen_id in range(json_size):
        
        citizen_dict = {
            'citizen_id': citizen_id + 1,
            'town': random.choice(DATA['town']),
            'street': random.choice(DATA['street']),
            'building': f'{random.randint(1, 100)}к{random.randint(1, 100)}стр{random.randint(1, 100)}',
            'apartment': random.randint(1, 100),
            'name': f"{random.choice(DATA['surname'])} {random.choice(DATA['name'])}",
            'birth_date': get_random_date(),
            'gender': random.choice(DATA['gender']),
            'relatives': []
        }

        citizens_list.append(citizen_dict)

    # Генерируются связи между родственниками
    MAX_VALUE = json_size * 10 #подобрано так, чтобы на 10к жителей было ~ 2к связей
    random_matrix = np.random.randint(MAX_VALUE, size=(json_size, json_size))
    random_binary_matrix = (random_matrix == MAX_VALUE - 1).astype(int)
    relatives_matrix = random_binary_matrix + random_binary_matrix.T
    

    print(json_size, np.sum(relatives_matrix))
    

    for citizen_id, relatives_row in enumerate(relatives_matrix, 1):
        for relative_id, is_connected in enumerate(relatives_row, 1):
            if is_connected:
                citizens_list[citizen_id - 1]['relatives'].append(relative_id)

    return citizens_list


if __name__ == '__main__':
    DATA = {}
    # TODO: убрать относительные пути и сделать нормально
    for filename in os.listdir('data'):
        data_name, _ = filename.split('.')
        with open(f'data/{filename}', 'rb') as f:
            DATA[data_name] = pickle.load(f)
        
        DATA['gender'] = ['male', 'female']

    samples_len = [1, 10, 50, 100, 1_000, 5_000, 10_000]
    for sample_len in samples_len:
        generated_json = {
            'citizens': generate_citizens_list(sample_len)
        }
        with open(f'samples/sample_{sample_len}.json', 'w') as f:
            f.write(json.dumps(generated_json))
