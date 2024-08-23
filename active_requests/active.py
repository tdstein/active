import re
from typing import Optional, TypeVar, Union
from urllib.parse import urljoin

import inflection
from requests import Session

from .interpolation import interpolate


T = TypeVar("T", bound="Active", covariant=True)

class ActiveBase(dict):
    session: Session = Session()
    url: str = "http://localhost"

    name: str  # the class name in lowercase
    path: str  # the plural name; represents the resource collection name
    uid: str = "id"  # the unique identifier field


class BelongsToAssociation(ActiveBase):

    belongs_to: Union[str, set[str], dict[str, str]]
    belongs_to_name: str
    belongs_to_path: str

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        if not hasattr(self, "belongs_to"):
            return

        belongs_to = getattr(self, "belongs_to")
        if isinstance(belongs_to, str):
            self.__associate(belongs_to, vars(self))
        elif isinstance(belongs_to, set):
            for each in belongs_to:
                self.__associate(each)
        elif isinstance(belongs_to, dict):
            for each, options in belongs_to.items():
                self.__associate(each, options)
        else:
            raise ValueError()

    def __associate(self, other, options={}):
        belongs_to_name = options.get("belongs_to_name", other)
        belongs_to_name = inflection.underscore(belongs_to_name)

        belongs_to_plural_name = inflection.pluralize(belongs_to_name)

        belongs_to_path = f"{belongs_to_plural_name}/:{belongs_to_name}_{self.uid}"
        belongs_to_path = options.get("has_one_path", belongs_to_path)
        belongs_to_path = interpolate(belongs_to_path, **self)

        # 'comments' => 'PostComments'
        assocation = inflection.camelize(self.name + "_" + belongs_to_name)
        bases = (Active,)
        Association = type(
            assocation,
            bases,
            {
                "url": self.url,
                "session": self.session,
                "name": belongs_to_name,
                "path": belongs_to_path,
            },
        )

        print(globals())

        setattr(self, belongs_to_name, Association)


class HasOneAssociation(ActiveBase):
    has_one: Union[str, set[str], dict[str, str]]
    has_one_name: str
    has_one_path: str

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        if not hasattr(cls, "has_one"):
            return

        has_one = getattr(cls, "has_one")
        if isinstance(has_one, str):
            cls.__associate(has_one, vars(cls))
        elif isinstance(has_one, set):
            for each in has_one:
                cls.__associate(each)
        elif isinstance(has_one, dict):
            for each, options in has_one.items():
                cls.__associate(each, options)
        else:
            raise ValueError()

    @classmethod
    def __associate(cls, other: str, options={}):
        has_one_name = options.get("has_one_name", other)
        has_one_name = inflection.underscore(has_one_name)

        has_one_path = f"{cls.path}/:{cls.uid}/{has_one_name}"
        has_one_path = options.get("has_one_path", has_one_path)

        has_one_endpoint = urljoin(cls.url, has_one_path)

        def fget(self):
            endpoint = interpolate(has_one_endpoint, **self)
            response = self.session.get(endpoint)
            response.raise_for_status()
            return response.json()

        def fset(self, **body):
            endpoint = interpolate(has_one_endpoint, **self)
            response = self.session.put(endpoint, json=body)
            response.raise_for_status()
            return

        def fdel(self):
            endpoint = interpolate(has_one_endpoint, **self)
            response = self.session.delete(endpoint)
            response.raise_for_status()
            return

        setattr(cls, has_one_name, property(fget, fset, fdel))


class HasManyAssociation(ActiveBase):

    has_many: Union[str, set[str], dict[str, str]]
    has_many_name: str
    has_many_path: str

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        if not hasattr(self, "has_many"):
            return

        has_many = getattr(self, "has_many")
        if isinstance(has_many, str):
            self.__associate(has_many, vars(self))
        elif isinstance(has_many, set):
            for each in has_many:
                self.__associate(each)
        elif isinstance(has_many, dict):
            for each, options in has_many.items():
                self.__associate(each, options)
        else:
            raise ValueError()

    def __associate(self, other, options={}):
        has_many_name = options.get("has_many_name", other)
        has_many_name = inflection.underscore(has_many_name)
        has_many_name = inflection.pluralize(has_many_name)

        has_many_path = f"{self.path}/:{self.uid}/{has_many_name}"
        has_many_path = options.get("has_one_path", has_many_path)
        has_many_path = interpolate(has_many_path, **self)

        # 'comments' => 'PostComments'
        assocation = inflection.camelize(self.name + "_" + has_many_name)
        bases = (Active,)
        Association = type(
            assocation,
            bases,
            {
                "url": self.url,
                "session": self.session,
                "name": has_many_name,
                "path": has_many_path,
            },
        )

        setattr(self, has_many_name, Association)


class ActiveAssociation(HasOneAssociation, HasManyAssociation):
    pass


class Active(ActiveAssociation, ActiveBase):

    endpoint: str  # the url and path

    def __init_subclass__(cls, url: Optional[str] = None, session: Optional[Session] = None, **kwargs):
        # Accept URL and session as class keyword arguments
        cls.url = url or cls.url
        cls.session = session or cls.session

        if hasattr(cls, "name"):
            name = getattr(cls, "name")
        else:
            name = inflection.underscore(cls.__name__)
            setattr(cls, "name", name)

        if hasattr(cls, "path"):
            path = getattr(cls, "path")
        else:
            path = inflection.pluralize(name)
            setattr(cls, "path", path)

        # Ensure the base attributes are set before calling super().__init_subclass__()
        # This guarantees that these attributes are derived from this class rather than the base class.
        super().__init_subclass__(**kwargs)

        if not hasattr(cls, "endpoint"):
            endpoint = urljoin(cls.url, cls.path)
            setattr(cls, "endpoint", endpoint)

    @classmethod
    def all(cls: type[T]) -> list[T]:
        response = cls.session.get(cls.endpoint)
        response.raise_for_status()
        body = response.json()
        return [cls(**kwargs) for kwargs in body]

    @classmethod
    def create(cls: type[T], **kwargs) -> T:
        response = cls.session.post(cls.endpoint, json=kwargs)
        response.raise_for_status()
        body = response.json()
        return cls(**body)

    @classmethod
    def find(cls: type[T], uid: str) -> T:
        endpoint = f"{cls.endpoint}/{uid}"
        response = cls.session.get(endpoint)
        response.raise_for_status()
        body = response.json()
        return cls(**body)

    @classmethod
    def find_by(cls: type[T], **conditions) -> Optional[T]:
        return next(iter(cls.where(**conditions)), None)

    @classmethod
    def first(cls: type[T]) -> Optional[T]:
        return next(iter(cls.all()), None)

    @classmethod
    def second(cls: type[T]) -> Optional[T]:
        return next(iter(cls.all()[1:]), None)

    @classmethod
    def third(cls: type[T]) -> Optional[T]:
        return next(iter(cls.all()[2:]), None)

    @classmethod
    def fourth(cls: type[T]) -> Optional[T]:
        return next(iter(cls.all()[3:]), None)

    @classmethod
    def fifth(cls: type[T]) -> Optional[T]:
        return next(iter(cls.all()[4:]), None)

    @classmethod
    def forty_two(cls: type[T]) -> Optional[T]:
        return next(iter(cls.all()[41:]), None)

    @classmethod
    def where(cls: type[T], **conditions) -> list[T]:
        response = cls.session.get(cls.endpoint, params=conditions)
        body = response.json()
        return [cls(**kwargs) for kwargs in body]

    def destroy(self) -> None:
        endpoint = f"{self.endpoint}/:{self.uid}"
        endpoint = interpolate(endpoint, **self)
        response = self.session.delete(endpoint)
        response.raise_for_status()

    def save(self) -> None:
        endpoint = f"{self.endpoint}/:{self.uid}"
        endpoint = interpolate(endpoint, **self)
        response = self.session.put(endpoint, json=self)
        response.raise_for_status()

    def update(self, **kwargs) -> None:
        super().update(**kwargs)
        self.save()
