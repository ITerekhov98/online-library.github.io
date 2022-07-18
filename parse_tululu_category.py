from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup


from requests import HTTPError, ConnectionError


def check_for_redirect(response):
    if response.history:
        raise HTTPError



def parse_books_collection(raw_html_page):
    base_url = 'https://tululu.org/'
    soup = BeautifulSoup(raw_html_page, 'lxml')
    books_details = soup.find('div', id='content').find_all('table', class_='d_book')
    books_ids = [
        details.find('div', class_='bookimage').find('a')['href'] for details in books_details
    ]
    books_urls = [
        urljoin(base_url, book_id) for book_id in books_ids
    ]
    return books_urls


def get_books_urls_from_page(collection_url):
    response = requests.get(collection_url)
    response.raise_for_status
    check_for_redirect(response)

    books_urls = parse_books_collection(response.text)
    return books_urls

def get_books_urls_from_collection(books_count):
    base_collection_url = 'https://tululu.org/l55/'
    books_urls = []
    current_page = 1
    while True:
        if len(books_urls) >= books_count:
            books_urls = books_urls[:books_count]
            return books_urls

        collection_url = urljoin(base_collection_url, str(current_page))
        try:
            books_urls.extend(get_books_urls_from_page(collection_url))
        except HTTPError:
            return books_urls
