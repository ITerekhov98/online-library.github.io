import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse, urljoin, quote

import requests
from requests import HTTPError, ConnectionError
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from retry import retry

from parse_tululu_category import   \
    get_books_urls_from_collection, \
    check_for_redirect


BOOKS_DIR = 'books'
IMAGES_DIR = 'images'

@dataclass
class Book:
    id: int
    title: str
    author: str
    image_url: str
    genres: list
    comments:list

    def get_readable_book_details(self, book_path, image_src):
        book_details = {
            'title': self.title,
            'author': self.author,
            'image_src': image_src,
            'book_path': book_path,
            'genres': self.genres,
            'comments': self.comments
        }
        return book_details

@retry(ConnectionError, delay=1, backoff=2, max_delay=128)
def download_book(book_details: Book, folder=BOOKS_DIR):
    url = 'https://tululu.org/txt.php'
    params = {
        'id': book_details.id
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    check_for_redirect(response)

    book_name = '{}. {}.txt'.format(
        book_details.id,
        sanitize_filename(book_details.title)
    )
    file_path = os.path.join(folder, book_name)
    with open(file_path, 'w') as file:
        file.write(response.text)
    return quote(file_path)


@retry(ConnectionError, delay=1, backoff=2, max_delay=128)
def download_image(image_url, folder=IMAGES_DIR):
    response = requests.get(image_url)
    response.raise_for_status()

    parced_url = urlparse(image_url)
    image_name = parced_url.path.split('/')[-1]
    image_path = os.path.join(folder, image_name)
    with open(image_path, 'wb') as file:
        file.write(response.content)
    return quote(image_path)


@retry(ConnectionError, delay=1, backoff=2, max_delay=128)
def get_book_page_by_id(book_id):
    url = f'https://tululu.org/b{book_id}/'
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)

    return url, response.text


@retry(ConnectionError, delay=1, backoff=2, max_delay=128)
def get_book_page_by_url(url):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)

    return response.text


def parse_book_details(url, raw_html_page):
    soup = BeautifulSoup(raw_html_page, 'lxml')
    cover_details = soup.select_one('#content').select_one('h1')
    title, author = cover_details.text.split('::')
    image_urn = soup.select_one('.bookimage img')['src']
    image_url = urljoin(url, image_urn)
    comments = [comment.text for comment in soup.select('.texts .black')]
    genres = [genre.text for genre in soup.select('span.d_book a')]

    parsed_url = urlparse(url)
    book_id = parsed_url.path[2:-1]

    book_details = Book(
        id= book_id,
        title= title.strip(),
        author= author.strip(),
        image_url= image_url,
        genres= genres,
        comments= comments
    )
    return book_details


def main():
    parser = argparse.ArgumentParser(
        description='Загрузка книг из онлайн-библиотеки tululu.org'
    )
    parser.add_argument(
        '--start_page',
        help='Начальная страница',
        type=int,
        default=1,
    )
    parser.add_argument(
        '--end_page',
        help='Конечная страница',
        type=int,
        default=float('inf'),
    )
    parser.add_argument(
        '--dest_folder',
        help='Каталог с результатами парсинга',
        default=os.getcwd(),
    )
    parser.add_argument(
        '--skip_imgs',
        help='Не скачивать фото',
        type=bool,
        default=False
    )
    parser.add_argument(
        '--skip_txt',
        help='не скачивать книги',
        type=bool,
        default=False
    )
    parser.add_argument(
        '--json_path',
        help='Путь к файлу с описанием книг',
        default=os.getcwd()
    )
    args = parser.parse_args()
    if not args.skip_txt:
        books_absolute_dir = os.path.join(args.dest_folder, BOOKS_DIR)
        Path(books_absolute_dir).mkdir(parents=True, exist_ok=True)
    if not args.skip_imgs:
        images_absolute_dir = os.path.join(args.dest_folder, IMAGES_DIR)
        Path(images_absolute_dir).mkdir(parents=True, exist_ok=True)

    books_urls = get_books_urls_from_collection(args)
    books_description = []
    for book_url in books_urls:
        try:
            raw_html_page = get_book_page_by_url(book_url)
            book_details = parse_book_details(book_url, raw_html_page)
            if not args.skip_txt:
                book_path = download_book(book_details)
            if not args.skip_imgs:
                image_src = download_image(book_details.image_url)
            books_description.append(
                book_details.get_readable_book_details(
                    book_path,
                    image_src,
                )
            )
        except HTTPError:
            sys.stdout.write(f'ссылка {book_url} невалидна\r\n')

    books_description_json = json.dumps(books_description, ensure_ascii=False)
    json_path = os.path.join(args.json_path, 'books_description.json')
    with open(json_path, 'w') as f:
        f.write(books_description_json)


if __name__ == '__main__':
    main()
