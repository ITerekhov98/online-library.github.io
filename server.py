import json

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import chunked


def on_reload():
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html'])
    )
    template = env.get_template('template.html')
    with open('books_description.json', 'r') as f:
        books_description = json.loads(f.read())
        books_pairs = chunked(books_description, 2)
    
    rendered_page = template.render(
        books_pairs=books_pairs
    )
    with open('index.html', 'w', encoding="utf8") as file:
        file.write(rendered_page)
    print("Site rebuilt")

on_reload()

server = Server()

server.watch('template.html', on_reload)

server.serve(root='.')