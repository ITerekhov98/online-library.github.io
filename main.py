from pathlib import Path

import requests

BOOKS_DIR = 'books'
Path(BOOKS_DIR).mkdir(parents=True, exist_ok=True)


def load_book(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text


for index in range(1, 11):
    book_url = f'https://tululu.org/txt.php?id={index}'
    book_path = f'{BOOKS_DIR}/id {index}.txt'
    with open (book_path, 'w') as file:
        file.write(load_book(book_url))

