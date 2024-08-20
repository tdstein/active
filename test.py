import unittest

import responses
from responses import matchers
from active import Active

class TestActive(unittest.TestCase):

    def test_get_name(self):

        class Comment(Active):
            pass

        assert Comment.name == "comment"

    def test_get_path(self):

        class Comment(Active):
            pass

        assert Comment.path == "comments"

    def test_get_endpoint(self):

        class Comment(Active):
            pass

        assert Comment.endpoint == "http://localhost/comments"

    @responses.activate
    def test_all(self):

        class Comment(Active):
            pass

        responses.get("http://localhost/comments", json=[{"key": "value"}])
        assert Comment.all() == [{"key": "value"}]

    @responses.activate
    def test_first(self):

        class Comment(Active):
            pass

        responses.get("http://localhost/comments", json=[{"key": "value"}])
        assert Comment.first() == {"key": "value"}

    @responses.activate
    def test_save(self):

        class Comment(Active):
            pass

        responses.put(
            "http://localhost/comments/1",
            match=[
                matchers.json_params_matcher({"id": 1}),
            ],
        )

        comment = Comment(id=1)
        comment.save()

    @responses.activate
    def test_update(self):

        class Comment(Active):
            pass

        responses.put(
            "http://localhost/comments/1",
            match=[
                matchers.json_params_matcher({"id": 1, "text": "Hello, World!"}),
            ],
        )

        comment = Comment(id=1)
        comment.update(text="Hello, World!")


class TestActiveAssociation(unittest.TestCase):

    @responses.activate
    def test_association_get(self):

        class Author(Active):
            pass

        class Book(Author, belongs_to=Author):
            pass

        assert hasattr(Book, "author")

        author = Author(id=1)
        responses.get("http://localhost/authors/1", json=author)

        book = Book(author_id=1)
        assert book.author == author

    @responses.activate
    def test_association_set(self):

        class Author(Active):
            pass

        class Book(Author, belongs_to=Author):
            pass

        assert hasattr(Book, "author")

        author = Author(id=1)

        book = Book()
        book.author = author
        assert book['author_id'] == 1


if __name__ == "__main__":
    unittest.main()
