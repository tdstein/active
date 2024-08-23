import unittest

import responses
from responses import matchers
from active_requests import Active


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
    def test_create(self):

        class Comment(Active):
            pass

        responses.post(
            "http://localhost/comments",
            json={"key": "value"},
            match=[
                matchers.json_params_matcher({"key": "value"}),
            ],
        )

        comment = Comment.create(key="value")
        assert comment == {"key": "value"}

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


# class TestHasOneAssociation(unittest.TestCase):


class TestGetHasOneName(unittest.TestCase):

    def test(self):
        class Author(Active):
            pass

        class Post(Active):
            has_one = Author

        assert Post.has_one == Author

    def test_is_type_str_pascal_case(self):

        class Post(Active):
            has_one = "Author"

        class Author(Active):
            pass

        post = Post()
        post.has_one == Author

    def test_is_type_str_snake_case(self):

        class Post(Active):
            has_one = "author"

        class Author(Active):
            pass

        post = Post()
        post.has_one == Author
