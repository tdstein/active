from requests import Session

from active_requests.active import Active


class Client(Session):
    def __init__(self, url, api_key) -> None:
        super().__init__()

        self.headers.update({"Authorization": f"Key {api_key}"})

        class Bundle(Active, url=url, session=self):
            "v1/bundles"

        class Content(Active, url=url, session=self):
            uid = "guid"
            name = "content"
            path = "v1/content"

            has_many = { "bundle", "permission", "job" }

            has_one = "vanity"

        class Environment(Active, url=url, session=self):
            path = "v1/environments"

        class Example(Active, url=url, session=self):
            path = 'v1/examples'

        class Job(Active, url=url, session=self):
            uid = "key"

        class Permission(Active, url=url, session=self):
            path = "v1/permissions"

        class OAuthSessions(Active, url=url, session=self):
            path = "v1/oauth/sessions"

        class Tag(Active, url=url, session=self):
            path = "v1/tags"

            belongs_to = {
                "tag": {
                    "belongs_to_name": "parent",
                    "belongs_to_path": "v1/tags/:parent_id",
                }
            }

            has_many = "content"
            has_many_name = "content"

        class Vanity(Active, url=url, session=self):
            path = "v1/vanities"

        self.bundles = Bundle
        self.content = Content
        self.environments = Environment
        self.examples = Example
        self.permissions = Permission
        self.sessions = OAuthSessions
        self.tags = Tag
        self.vanities = Vanity


if __name__ == "__main__":
    c = Client("https://rsc.radixu.com/__api__/", "pYFqLjm5idHnr9zruRz8ANdaSlaH8fe5")

    content = c.content.find("8ea6fb4a-8fb3-4c22-8c64-a152789d2c23")
    print(content)
    print(content.vanity)
    print(c.sessions.all())
    # print(tag.parent)
    # print(tag.parent.parent)
    # print(tag.parent.parent.parent)
    # print(tag.parent.parent.parent.parent)
    # print(tag.parent.parent.parent.parent.parent)
