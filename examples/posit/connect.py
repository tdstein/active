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

            has_many = { "Bundle", "Permission", "Job" }

        class Job(Active, url=url, session=self):
            uid = "key"

        class Permission(Active, url=url, session=self):
            path = "v1/permissions"

        class Tag(Active, url=url, session=self):
            path = "v1/tags"

            has_one = {
                "Tag": {
                    "has_one_name": "parent",
                    "has_one_path": "v1/tags/:parent_id",
                }
            }

            has_many = {
                Content: {
                    'has_many_path': 'v1/tags/:id/content'
                },
            }

        self.bundle = Bundle
        self.content = Content
        self.permission = Permission
        self.tag = Tag


if __name__ == "__main__":
    c = Client("https://rsc.radixu.com/__api__/", "pYFqLjm5idHnr9zruRz8ANdaSlaH8fe5")
    content = c.content.second()
    print(content)
    bundle = content.bundles.first()
    print(bundle)

    tag = c.tag.find_by(name="qwrqwr")
    print(tag)
    print(tag)
    print(tag.parent)
    print(tag.parent.parent)
    print(tag.parent.parent.parent)
    print(tag.parent.parent.parent.parent)
    print(tag.parent.parent.parent.parent.parent)
