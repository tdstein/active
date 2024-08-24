from active_requests import Active

Active.url = "http://jsonplaceholder.typicode.com"


class Post(Active):
    belongs_to = "user"
    belongs_to_path = "/users/:userId"

    has_many = "Comment"


class Comment(Active):
    belongs_to = {"post": {"belongs_to_path": "posts/:postId"}}


class Album(Active):
    belongs_to = {"user": {"belongs_to_path": "users/:userId"}}

    has_many = "Photo"


class Photo(Active):
    belongs_to = {"album": {"belongs_to_path": "albums/:albumId"}}


class Todo(Active):
    belongs_to = {"user": {"belongs_to_path": "users/:userId"}}


class User(Active):
    has_many = {"Album", "Post", "Todo"}


for post in Post.all()[::10]:
    print(post['id'])
    print(post.user.posts.first()['id'])
