from http import client
import os
from requests import Session

from active_requests.active import Active

api_key = os.environ["CONNECT_API_KEY"]

session = Session()
session.headers.update({"Authorization": f"Key {api_key}"})

Active.url = "https://rsc.radixu.com/__api__/"
Active.session = session

class Bundle(Active):
    path = "v1/bundles"

class Content(Active):
    name = "content"
    path = "v1/content"
    uid = "guid"

    has_many = { "bundle", "permission", "job", "tags" }

    has_one = "vanity"


class Environment(Active):
    path = "v1/environments"

class Example(Active):
    path = 'v1/examples'

class Job(Active):
    uid = "key"

class Permission(Active):
    path = "v1/permissions"

class OAuthSessions(Active):
    path = "v1/oauth/sessions"

class Tag(Active):
    path = "v1/tags"

    belongs_to = {
        "tag": {
            "belongs_to_name": "parent",
            "belongs_to_path": "v1/tags/:parent_id",
        }
    }

    has_many = "content"
    has_many_name = "content"

class Vanity(Active):

    belongs_to = "Content"
    belongs_to_path = "v1/content/:content_guid"


if __name__ == "__main__":

    client.content.find()

    content = Content.find_by(title="Developing Machine Learning Models with Airflow and Posit Connect")
    content.vanity = { "path": "developing-machine-learning-models-with-airflow-and-posit-connect"}
    print(content.vanity.content['title'])

    tags = content.tags.all()
    for tag in tags:
        print(tag['name'])

    bundle = content.bundles.first()
    print(bundle["created_time"])
