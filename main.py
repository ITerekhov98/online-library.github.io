import argparse
import os
from pathlib import Path
from urllib.parse import urlparse, urljoin

import requests
from requests import HTTPError
from pathvalidate import sanitize_filename
from bs4 import BeautifulSoup


BOOKS_DIR = 'books'
IMAGES_DIR = 'images'
Path(BOOKS_DIR).mkdir(parents=True, exist_ok=True)
Path(IMAGES_DIR).mkdir(parents=True, exist_ok=True)


def check_for_redirect(response):
    if response.history:
        raise HTTPError


def download_book(book_id, book_name, folder=BOOKS_DIR):
    url = 'https://tululu.org/txt.php'
    params = {
        'id': book_id
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    check_for_redirect(response)

    book_name = f'{book_id}. {sanitize_filename(book_name)}.txt'
    file_path = os.path.join(folder, book_name)
    with open(file_path, 'w') as file:
        file.write(response.text)
    return file_path


def download_image(book_url, folder=IMAGES_DIR):
    url = urljoin('https://tululu.org/', book_url)
    response = requests.get(url)
    response.raise_for_status()

    parced_url = urlparse(url)
    image_name = parced_url.path.split('/')[-1]
    image_path = os.path.join(folder, image_name)
    with open(image_path, 'wb') as file:
        file.write(response.content)


def get_book_details(book_id):
    url = f'https://tululu.org/b{book_id}/'
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)

    soup = BeautifulSoup(response.text, 'lxml')
    cover_details = soup.find('div', id='content').find('h1')
    title, author = cover_details.text.split('::')
    image_url = soup.find('div', class_='bookimage').find('img')['src']
    raw_comments = soup.find_all('div', class_='texts')
    comments = [
        comment.find('span', class_='black').text for comment in raw_comments
    ]
    raw_genres = soup.find('span', class_='d_book').find_all('a')
    genres = [genre.text for genre in raw_genres]

    book_details = {
        'title': title.strip(),
        'author': author.strip(),
        'image_url': image_url,
        'comments': comments,
        'genres': genres
    }
    return book_details


def main():
    parser = argparse.ArgumentParser(
        description='Загрузка книг из онлайн-библиотеки tululu.org'
    )
    parser.add_argument(
        'start_id',
        help='Укажите с какого id начинать загрузку',
        type=int
    )
    parser.add_argument(
        'end_id',
        help='Укажите на каком id закончить загрузку',
        type=int
    )
    args = parser.parse_args()

    for book_id in range(args.start_id, args.end_id + 1):
        try:
            book_details = get_book_details(book_id)
            download_book(book_id, book_details['title'])
            download_image(book_details['image_url'])
        except HTTPError:
            print(f'{book_id} invalid')


if __name__ == '__main__':
    main()
