from pathlib import Path
import os
import requests
from requests import HTTPError
from pathvalidate import sanitize_filename
from bs4 import BeautifulSoup


BOOKS_DIR = 'books'
Path(BOOKS_DIR).mkdir(parents=True, exist_ok=True)


def download_book(url, file_name, folder=BOOKS_DIR):
    file_name = f'{sanitize_filename(file_name)}.txt'
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    file_path = os.path.join(folder, file_name)
    with open(file_path, 'w') as file:
        file.write(response.text)
    return file_path

def get_book_details(book_id):
    url = f'https://tululu.org/b{book_id}/'
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    soup = BeautifulSoup(response.text, 'lxml')
    book_details = soup.find('div', id='content').find('h1')
    title, author = book_details.text.split('::')
    book_details = {
        'title': title.strip(),
        'author': author.strip()
    }
    return book_details

def check_for_redirect(response):
    if response.history:
        raise HTTPError

for index in range(1, 11):
    book_url = f'https://tululu.org/txt.php?id={index}'
    try:
        book_details = get_book_details(index)
        book_name = f"{index}. {book_details['title']}" 
        download_book(book_url, book_name)
    except HTTPError:
        print(f'{book_url} invalid')
        continue


