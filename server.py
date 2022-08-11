import json
import os
from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import chunked
from math import ceil
from functools import partial


BOOKS_COUNT_PER_PAGE = 20

def on_reload(env):
    template = env.get_template('template.html')
    with open('books_description.json', 'r') as f:
        books_description = json.load(f)

    number_of_pages = ceil(len(books_description) / BOOKS_COUNT_PER_PAGE)
    for index, books_batch in enumerate(chunked(books_description, BOOKS_COUNT_PER_PAGE), start=1):
        rendered_page = template.render(
            books_pairs=chunked(books_batch, 2),
            number_of_pages=number_of_pages,
            current_page_number=index
        )
        current_page = f'index{index}.html'
        with open(f'pages/{current_page}', 'w', encoding="utf8") as file:
            file.write(rendered_page)
    print("Site rebuilt")


def main():
    os.makedirs('pages', exist_ok=True)
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html'])
    )
    on_reload(env)
    server = Server()
    server.watch('template.html', partial(on_reload, env))    
    server.serve(root='.', default_filename='pages/index1.html')


if __name__ == '__main__':
    main()