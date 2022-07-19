import argparse
import os
import json
from pathlib import Path
from urllib.parse import urlparse, urljoin

import requests
from requests import HTTPError, ConnectionError
from retry import retry
from pathvalidate import sanitize_filename
from bs4 import BeautifulSoup

from parse_tululu_category import get_books_urls_from_collection, check_for_redirect


BOOKS_DIR = 'books'
IMAGES_DIR = 'images'
BOOKS_INFO_DIR = 'books_info'





@retry(ConnectionError, delay=1, backoff=2, max_delay=128)
def download_book(book_details, folder=BOOKS_DIR):
    url = 'https://tululu.org/txt.php'
    params = {
        'id': book_details['id']
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    check_for_redirect(response)

    book_name = f"{book_details['id']}. {sanitize_filename(book_details['title'])}.txt"
    file_path = os.path.join(folder, book_name)
    with open(file_path, 'w') as file:
        file.write(response.text)
    return file_path


@retry(ConnectionError, delay=1, backoff=2, max_delay=128)
def download_image(image_url, folder=IMAGES_DIR):
    response = requests.get(image_url)
    response.raise_for_status()

    parced_url = urlparse(image_url)
    image_name = parced_url.path.split('/')[-1]
    image_path = os.path.join(folder, image_name)
    with open(image_path, 'wb') as file:
        file.write(response.content)
    return image_path


def get_readable_book_info(book_details, book_path, image_src):
    del book_details['image_url']
    del book_details['id']
    book_details['image_src'] = image_src
    book_details['book_path'] = book_path
    return book_details


def save_extra_info(book_id, book_details, folder=BOOKS_INFO_DIR):
    file_path = os.path.join(folder, f'{book_id}.txt')
    with open(file_path, 'w') as file:
        for description, data in book_details.items():
            if description == 'comments':
                file.write('comments:\r\n')
                [file.writelines(f'{comment}\r\n') for comment in data]
            else:
                file.write(f'{description}: {data}\r\n')


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
    
    book_details = {
        'id': book_id,
        'title': title.strip(),
        'author': author.strip(),
        'image_url': image_url,
        'genres': genres,
        'comments': comments,
    }
    return book_details


def main():
    Path(BOOKS_DIR).mkdir(parents=True, exist_ok=True)
    Path(IMAGES_DIR).mkdir(parents=True, exist_ok=True)
    parser = argparse.ArgumentParser(
        description='Загрузка книг из онлайн-библиотеки tululu.org'
    )
    parser.add_argument(
        '--start_page',
        help='Начальная страница',
        type=int,
        default = 1,
    )
    parser.add_argument(
        '--end_page',
        help='Конечная страница',
        type=int,
        default = float('inf'),
    )
    loading_pages = parser.parse_args()
    books_urls = get_books_urls_from_collection(loading_pages)
    books_info = []
    for book_url in books_urls:
        try:
            raw_html_page = get_book_page_by_url(book_url)
            book_details = parse_book_details(book_url, raw_html_page)
            book_path = download_book(book_details)
            image_src = download_image(book_details['image_url'])
            books_info.append(
                get_readable_book_info(
                    book_details, 
                    book_path,
                    image_src
                )
            )
        except HTTPError:
            print(f'{book_url} invalid')

    books_info_json = json.dumps(books_info, ensure_ascii=False)
    with open('books_info.json', 'w') as f:
        f.write(books_info_json)


if __name__ == '__main__':
    main()
