from typing import Callable, Optional, TypeVar, TypedDict, Union
from urllib.parse import urljoin

import inflection
from requests import Session

from .interpolation import interpolate


T = TypeVar("T", bound="Active", covariant=True)

_registry: dict[str, type[T]] = {}


def register(name: str, cls: type[T]):
    name = inflection.underscore(name)
    _registry[name] = cls


def resolve(name: str) -> Optional[type[T]]:
    name = inflection.underscore(name)
    return _registry.get(name)


class ActiveBase(dict):
    session: Session = Session()
    url: str = "http://localhost"

    name: str
    path: str
    uid: str = "id"


class BelongsToOptions(TypedDict, total=False):
    belongs_to_name: Optional[str]
    belongs_to_path: Optional[str]


class HasOneOptions(TypedDict, total=False):
    has_one_name: Optional[str]
    has_one_path: Optional[str]


class HasManyOptions(TypedDict, total=False):
    has_many_name: Optional[str]
    has_many_path: Optional[str]


AssociationOptions = Union[BelongsToOptions, HasManyOptions, HasOneOptions]
AssociationDef = Union[str, set[str], dict[str, AssociationOptions]]


class AssociationBase:
    @classmethod
    def _associate(
        cls,
        association: AssociationDef,
        associate_method: Callable,
    ):
        if isinstance(association, str):
            associate_method(association, vars(cls))

        if isinstance(association, set):
            for each in association:
                associate_method(each)

        if isinstance(association, dict):
            for each, options in association.items():
                associate_method(each, options)


class BelongsToAssociation(ActiveBase, AssociationBase):
    belongs_to: Union[str, set[str], dict[str, BelongsToOptions]]
    belongs_to_name: str
    belongs_to_path: str

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__()
        if hasattr(cls, "belongs_to"):
            belongs_to = getattr(cls, "belongs_to")
            cls._associate(belongs_to, cls.__associate)

    @classmethod
    def __associate(cls, other: str, options: BelongsToOptions = {}):
        if "belongs_to_name" in options:
            belongs_to_name = options["belongs_to_name"]
            belongs_to_name = inflection.underscore(belongs_to_name)
        else:
            belongs_to_name = inflection.underscore(other)

        if "belongs_to_path" in options:
            belongs_to_path = options["belongs_to_path"]
        else:
            belongs_to_name_plural = inflection.pluralize(belongs_to_name)
            belongs_to_path = f"{belongs_to_name_plural}/:{belongs_to_name}_{cls.uid}"

        def fget(self):
            path = interpolate(belongs_to_path, **self)
            endpoint = urljoin(self.url, path)
            endpoint = interpolate(endpoint, **self)
            response = self.session.get(endpoint)
            response.raise_for_status()
            result = response.json()
            cls = resolve(other)
            return cls(**result) if cls else result

        def fset(self, body):
            path = interpolate(belongs_to_path, **self)
            endpoint = urljoin(self.url, path)
            endpoint = interpolate(endpoint, **self)
            response = self.session.put(endpoint, json=body)
            response.raise_for_status()
            return

        def fdel(self):
            path = interpolate(belongs_to_path, **self)
            endpoint = urljoin(self.url, path)
            endpoint = interpolate(endpoint, **self)
            response = self.session.delete(endpoint)
            response.raise_for_status()
            return

        setattr(cls, belongs_to_name, property(fget, fset, fdel))


class HasOneAssociation(ActiveBase, AssociationBase):
    has_one: Union[str, set[str], dict[str, HasOneOptions]]
    has_one_name: str
    has_one_path: str

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        if hasattr(cls, "has_one"):
            has_one = getattr(cls, "has_one")
            cls._associate(has_one, cls.__associate)

    @classmethod
    def __associate(cls, other: str, options: HasOneOptions = {}):
        other = inflection.underscore(other)
        if "has_one_name" in options:
            has_one_name = options["has_one_name"]
        else:
            has_one_name = inflection.underscore(other)

        if "has_one_path" in options:
            has_one_path = options["has_one_path"]
        else:
            has_one_path = f"{cls.path}/:{cls.uid}/{has_one_name}"

        has_one_endpoint = urljoin(cls.url, has_one_path)

        def fget(self: Active):
            endpoint = interpolate(has_one_endpoint, **self)
            response = self.session.get(endpoint)
            if response.status_code == 404:
                return None

            response.raise_for_status()
            result = response.json()
            cls = resolve(other)
            return cls(**result) if cls else result

        def fset(self, body):
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


class HasManyAssociation(ActiveBase, AssociationBase):
    has_many: Union[str, set[str], dict[str, HasManyOptions]]
    has_many_name: str
    has_many_path: str

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        if hasattr(self, "has_many"):
            has_many = getattr(self, "has_many")
            self._associate(has_many, self.__associate)

    def __associate(self, other: str, options: HasManyOptions = {}):
        if "has_many_name" in options:
            has_many_name = options["has_many_name"]
        else:
            has_many_nane = inflection.underscore(other)
            has_many_name = inflection.pluralize(has_many_nane)

        if "has_many_path" in options:
            has_many_path = options["has_many_path"]
        else:
            has_many_path = f"{self.path}/:{self.uid}/{has_many_name}"

        has_many_path = interpolate(has_many_path, **self)

        Association = resolve(other)
        if Association:
            bases = Association.__bases__
            kwds = dict(vars(Association))
        else:
            bases = (Active,)
            kwds = {}

        Association = type(
            inflection.camelize(self.name + "_" + has_many_name),
            bases,
            {
                **kwds,
                "url": self.url,
                "session": self.session,
                "name": has_many_name,
                "path": has_many_path,
            },
        )

        setattr(self, has_many_name, Association)


class ActiveAssociation(BelongsToAssociation, HasOneAssociation, HasManyAssociation):
    pass


class Active(ActiveAssociation, ActiveBase):
    endpoint: str  # the url and path

    def __init_subclass__(
        cls, url: Optional[str] = None, session: Optional[Session] = None, **kwargs
    ):
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

        register(name, cls)

        super().__init_subclass__(**kwargs)

        endpoint = urljoin(cls.url, cls.path)
        setattr(cls, "endpoint", endpoint)

    @classmethod
    def all(cls: type[T], **params) -> list[T]:
        response = cls.session.get(cls.endpoint, params=params)
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
    def first(cls: type[T], **params) -> Optional[T]:
        return next(iter(cls.all(**params)), None)

    @classmethod
    def second(cls: type[T], **params) -> Optional[T]:
        return next(iter(cls.all(**params)[1:]), None)

    @classmethod
    def third(cls: type[T], **params) -> Optional[T]:
        return next(iter(cls.all(**params)[2:]), None)

    @classmethod
    def fourth(cls: type[T], **params) -> Optional[T]:
        return next(iter(cls.all(**params)[3:]), None)

    @classmethod
    def fifth(cls: type[T], **params) -> Optional[T]:
        return next(iter(cls.all(**params)[4:]), None)

    @classmethod
    def forty_two(cls: type[T], **params) -> Optional[T]:
        return next(iter(cls.all(**params)[41:]), None)

    @classmethod
    def where(cls: type[T], **conditions) -> list[T]:
        results = cls.all()
        def matches(result):
            return all(result.get(k) == v for k, v in conditions.items())
        results = filter(matches, results)
        return [cls(**kwargs) for kwargs in results]

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


    def update(self, *args, **kwargs) -> None:
        super().update(*args, **kwargs)
        self.save()
