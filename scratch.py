from __future__ import annotations


class Active(dict):
    pass

class Author(Active):

    has_one = "Profile"
    has_one_path = "/profiles/:profile"

    has_many = "Book"
    has_many_path = '/authors/:author_id/books'


class Profile(Active):

    belongs_to = Author
    belongs_to_path = ""


class Book(Active):
    belongs_to = Author
    belongs_to_path = "/authors/:author_id/books"

book = Book(id=1, title="Lord of the Rings", author_id=1)

# create the author
# capture the author
# set book['author_id'] = author['id']
# return author
author = book.create_author(name='J. R. R. Tolkien')
