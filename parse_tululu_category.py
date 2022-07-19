from urllib.parse import urljoin

import requests
from requests import HTTPError, ConnectionError
from bs4 import BeautifulSoup
from retry import retry


def check_for_redirect(response):
    if response.history:
        raise HTTPError


def parse_books_collection(raw_html_page):
    base_url = 'https://tululu.org/'
    soup = BeautifulSoup(raw_html_page, 'lxml')
    books_ids = [
        el["href"] for el in soup.select('.d_book .bookimage a')
    ]
    books_urls = [
        urljoin(base_url, book_id) for book_id in books_ids
    ]
    return books_urls


@retry(ConnectionError, delay=1, backoff=2, max_delay=128)
def get_books_urls_from_page(collection_url):
    response = requests.get(collection_url)
    response.raise_for_status
    check_for_redirect(response)

    books_urls = parse_books_collection(response.text)
    return books_urls


def get_books_urls_from_collection(args):
    base_collection_url = 'https://tululu.org/l55/'
    books_urls = []
    for page in range(args.start_page, args.end_page):
        collection_url = urljoin(base_collection_url, str(page))
        try:
            books_urls.extend(get_books_urls_from_page(collection_url))
        except HTTPError:
            return books_urls
    return books_urls
