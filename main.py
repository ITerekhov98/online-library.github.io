from pathlib import Path
import os
import requests
from requests import HTTPError
from pathvalidate import sanitize_filename
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin


BOOKS_DIR = 'books'
Path(BOOKS_DIR).mkdir(parents=True, exist_ok=True)
IMAGES_DIR = 'images'
Path(IMAGES_DIR).mkdir(parents=True, exist_ok=True)


def download_book(url, file_name, folder=BOOKS_DIR):
    file_name = f'{sanitize_filename(file_name)}.txt'
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    file_path = os.path.join(folder, file_name)
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
    book_details = soup.find('div', id='content').find('h1')
    title, author = book_details.text.split('::')
    image_url = soup.find('div', class_='bookimage').find('img')['src']
    raw_comments = soup.find_all('div', class_='texts')
    comments = [comment.find('span', class_='black').text for comment in raw_comments]
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

def check_for_redirect(response):
    if response.history:
        raise HTTPError

for index in range(1, 11):
    book_url = f'https://tululu.org/txt.php?id={index}'
    try:
        book_details = get_book_details(index)
        book_name = f"{index}. {book_details['title']}" 
        print(book_details['comments'])
        print(book_details['genres'])
        # download_image(book_details['image_url'])
        # download_book(book_url, book_name)
    except HTTPError:
        print(f'{book_url} invalid')
        continue


