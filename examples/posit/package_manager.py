from active_requests import Active

Active.url = "https://packagemanager.posit.co/__api__/"

class Alert(Active):
    pass

class BlocklistRule(Active):
    path = "blocklist/rules"

class Package(Active):
    has_many = {
        "binary",
        "sysreq"
    }

class Repo(Active):
    uid = "name"
    has_many = {
        "binary",
        "package",
        "source",
        "sysreq",
        "vuln"
    }

class Source(Active):
    has_many = {
        "package",
        "transaction",
        "vuln"
    }

class Vuln(Active):
    uid = "key"

    belongs_to = {
        "repo",
        "source"
    }

for repo in Repo.all():
    print(repo["name"])

repo = Repo.find_by(name="pypi")
binaries = repo.binaries.all(distribution="focal", r_version="4.4", packages="requests")
print(binaries)

print(repo.packages.first().binaries)
