import json
import os
from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import chunked


def on_reload():
    os.makedirs('pages', exist_ok=True)
    with open('books_description.json', 'r') as f:
        books_description = json.loads(f.read())

    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html'])
    )
    template = env.get_template('template.html')
    for index, books_batch in enumerate(chunked(books_description, 20), start=1):
        rendered_page = template.render(
            books_pairs=chunked(books_batch, 2)
        )
        current_page = f'index{index}.html'
        with open(f'pages/{current_page}', 'w', encoding="utf8") as file:
            file.write(rendered_page)
    print("Site rebuilt")

on_reload()

server = Server()

server.watch('template.html', on_reload)

server.serve(root='.')