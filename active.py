from typing import Generic, Optional, Type, TypeVar
from urllib.parse import urljoin
from requests import Session

R = TypeVar("R", bound="Active", covariant=True)


class ActiveAssociation:

    def __init_subclass__(
        cls: type["Active"],
        /,
        belongs_to: Optional[type["Active"]] = None,
        **kwargs
    ) -> None:
        super().__init_subclass__()
        if belongs_to:
            fuid = belongs_to.name + '_' + belongs_to.uid
            def fget(self):
                return belongs_to.find(self[fuid])

            def fset(self, value: Active):
                self[fuid] = value[value.uid]

            def fdel(self):
                del self[fuid]

            association = property(fget, fset, fdel)
            setattr(cls, belongs_to.name, association)


class Active(Generic[R], dict, ActiveAssociation):

    name: str       # the class name in lowercase
    path: str       # the plural name; represents the resource collection name
    endpoint: str   # the url and path

    session: Session = Session()
    url: str = "http://localhost"
    uid: str = "id"

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "name"):
            name = cls.__name__.lower()
            setattr(cls, "name", name)

        if not hasattr(cls, "path"):
            path = name + "s"
            setattr(cls, "path", path)

        if not hasattr(cls, "endpoint"):
            endpoint = urljoin(cls.url, path)
            setattr(cls, "endpoint", endpoint)

    @classmethod
    def all(cls: type[R]) -> list[R]:
        response = cls.session.get(cls.endpoint)
        body = response.json()
        return [cls(**kwargs) for kwargs in body]

    @classmethod
    def find(cls: type[R], uid: str) -> R:
        endpoint = f"{cls.endpoint}/{uid}"
        response = cls.session.get(endpoint)
        response.raise_for_status()
        body = response.json()
        return cls(**body)

    @classmethod
    def find_by(cls: type[R], **conditions) -> Optional[R]:
        return next(iter(cls.where(**conditions)), None)

    @classmethod
    def first(cls: type[R]) -> Optional[R]:
        return next(iter(cls.all()), None)

    @classmethod
    def where(cls: type[R], **conditions) -> list[R]:
        response = cls.session.get(cls.endpoint, params=conditions)
        body = response.json()
        return [cls(**kwargs) for kwargs in body]

    def destroy(self) -> None:
        endpoint = f"{self.endpoint}/{self[self.uid]}"
        response = self.session.delete(endpoint)
        response.raise_for_status()

    def save(self) -> None:
        endpoint = f"{self.endpoint}/{self[self.uid]}"
        response = self.session.put(endpoint, json=self)
        response.raise_for_status()

    def update(self, **kwargs) -> None:
        super().update(**kwargs)
        self.save()
