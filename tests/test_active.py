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

class TestBelongsToPropertyName(unittest.TestCase):
    def test(self):
        class Comment(Active):
            belongs_to = 'post'

        assert hasattr(Comment, 'post')

    def test_is_pascal_case(self):
        class Comment(Active):
            belongs_to = "Post"

        assert hasattr(Comment, "post")


class TestBelongsToShape(unittest.TestCase):

    def test_is_str(self):
        class Comment(Active):
            belongs_to = "Post"

    def test_is_set(self):
        class Comment(Active):
            belongs_to = { "Post" }

    def test_is_dict(self):
        class Comment(Active):
            belongs_to = {
                "Post": {}
            }

    def test_is_None(self):
        try:
            class Comment(Active):
                belongs_to = None
        except ValueError:
            pass

    def test_is_1(self):
        try:
            class Comment(Active):
                belongs_to = 1
        except ValueError:
            pass

    def test_is_class(self):
        try:

            class Post:
                pass
            class Comment(Active):
                belongs_to = Post

        except ValueError:
            pass



class TestGetHasOneName(unittest.TestCase):

    def test(self):
        class Post(Active):
            has_one = "author"

        hasattr(Post, 'author')

    def test_is_type_str_pascal_case(self):

        class Post(Active):
            has_one = "Author"

        hasattr(Post, 'author')

    def test_is_type_str_snake_case(self):

        class Post(Active):
            has_one = "author"

        hasattr(Post, "author")
