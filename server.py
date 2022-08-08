import json

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server


def on_reload():
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html'])
    )
    template = env.get_template('template.html')
    with open('books_description.json', 'r') as f:
        books_description = f.read()
    
    rendered_page = template.render(
        books_description=json.loads(books_description)
    )
    with open('index.html', 'w', encoding="utf8") as file:
        file.write(rendered_page)
    print("Site rebuilt")

on_reload()

server = Server()

server.watch('template.html', on_reload)

server.serve(root='.')