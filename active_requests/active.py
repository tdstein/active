import copy
from typing import Callable, Optional, TypeVar, TypedDict, Union
from urllib.parse import urljoin

import inflection
from requests import Session

from .interpolation import interpolate


T = TypeVar("T", bound="Active", covariant=True)

_registry = {}


def register(name: str, cls: type["Active"]):
    """
    Register a class with a given name in the global registry.

    :param name: The name to register the class under.
    :type name: str
    :param cls: The class to register.
    :type cls: type[Active]
    """
    name = inflection.underscore(name)
    _registry[name] = cls


def resolve(name: str) -> Optional[type["Active"]]:
    """
    Resolve a class from the global registry by name.

    :param name: The name of the class to resolve.
    :type name: str
    :return: The resolved class or None if not found.
    :rtype: Optional[type[Active]]
    """
    name = inflection.underscore(name)
    return _registry.get(name)


class ActiveBase(dict):
    """
    Base class for Active classes.

    :cvar session: The session used for HTTP requests.
    :cvar url: The base URL for the API.
    :cvar name: The class name in lowercase.
    :cvar path: The plural name representing the resource collection name.
    :cvar uid: The unique identifier field.
    """

    session: Session = Session()
    url: str = "http://localhost"

    name: str
    path: str
    uid: str = "id"


class BelongsToOptions(TypedDict, total=False):
    """
    TypedDict for options used in the __associate method of BelongsToAssociation.

    :key belongs_to_name: Custom name for the 'belongs_to' association.
    :type belongs_to_name: Optional[str]
    :key belongs_to_path: Custom path for the 'belongs_to' association.
    :type belongs_to_path: Optional[str]
    """

    belongs_to_name: Optional[str]
    belongs_to_path: Optional[str]


class HasOneOptions(TypedDict, total=False):
    """
    TypedDict for options used in the __associate method of HasOneAssociation.

    :key has_one_name: Custom name for the 'has_one' association.
    :type has_one_name: Optional[str]
    :key has_one_path: Custom path for the 'has_one' association.
    :type has_one_path: Optional[str]
    """

    has_one_name: Optional[str]
    has_one_path: Optional[str]


class HasManyOptions(TypedDict, total=False):
    """
    TypedDict for options used in the __associate method of HasManyAssociation.

    :key has_many_name: Custom name for the 'has_many' association.
    :type has_many_name: Optional[str]
    :key has_many_path: Custom path for the 'has_many' association.
    :type has_many_path: Optional[str]
    """

    has_many_name: Optional[str]
    has_many_path: Optional[str]


AssociationOptions = Union[BelongsToOptions, HasManyOptions, HasOneOptions]
AssociationDef = Union[str, set[str], dict[str, AssociationOptions]]
"""
Type alias representing the structure of an association definition.

- **str**: A single association, represented by a string (e.g., `"author"`).
- **set[str]**: Multiple associations, represented by a set of strings (e.g., `{"author", "publisher"}`).
- **dict[str, AssociationOptions]**: Associations with options, where the key is the association name and the value is the option set (e.g., `{"author": {}}`).
"""


class AssociationBase:
    """
    Base class for handling associations.
    """

    @classmethod
    def _associate(
        cls,
        association: AssociationDef,
        associate_method: Callable[[str, Optional[AssociationOptions]], None],
    ):
        """
        Associate attributes based on the type of association.

        :param association: The association definition, which can be a string, set of strings, or a dictionary.
        :type association: AssociationDef
        :param associate_method: The method to call for associating.
        :type associate_method: Callable[[str, Optional[AssociationOptions]], None]
        """
        if isinstance(association, str):
            associate_method(association, vars(cls))

        if isinstance(association, set):
            for each in association:
                associate_method(each)

        if isinstance(association, dict):
            for each, options in association.items():
                associate_method(each, options)


class BelongsToAssociation(ActiveBase, AssociationBase):
    """
    Represents a 'belongs_to' association.

    :cvar belongs_to: The 'belongs_to' relationship definition.
    :cvar belongs_to_name: The name of the associated resource.
    :cvar belongs_to_path: The path to the associated resource.
    """

    belongs_to: Union[str, set[str], dict[str, BelongsToOptions]]
    belongs_to_name: str
    belongs_to_path: str

    def __init_subclass__(cls, **kwargs) -> None:
        """
        Automatically associate the 'belongs_to' relationship when subclassing.
        """
        super().__init_subclass__()
        if hasattr(cls, "belongs_to"):
            belongs_to = getattr(cls, "belongs_to")
            cls._associate(belongs_to, cls.__associate)

    @classmethod
    def __associate(cls, other: str, options: BelongsToOptions = {}):
        """
        Associate a 'belongs_to' relationship.

        :param other: The other resource to associate with.
        :type other: str
        :param options: Additional options for the association.
        :type options: BelongsToOptions
        """
        other = inflection.underscore(other)
        belongs_to_name = options.get("belongs_to_name", other)
        belongs_to_name = inflection.underscore(belongs_to_name)

        belongs_to_name_plural = inflection.pluralize(belongs_to_name)

        belongs_to_path = f"{belongs_to_name_plural}/:{belongs_to_name}_{cls.uid}"
        belongs_to_path = options.get("belongs_to_path", belongs_to_path)

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
    """
    Represents a 'has_one' association.

    :cvar has_one: The 'has_one' relationship definition.
    :cvar has_one_name: The name of the associated resource.
    :cvar has_one_path: The path to the associated resource.
    """

    has_one: Union[str, set[str], dict[str, HasOneOptions]]
    has_one_name: str
    has_one_path: str

    def __init_subclass__(cls) -> None:
        """
        Automatically associate the 'has_one' relationship when subclassing.
        """
        super().__init_subclass__()
        if hasattr(cls, "has_one"):
            has_one = getattr(cls, "has_one")
            cls._associate(has_one, cls.__associate)

    @classmethod
    def __associate(cls, other: str, options: HasOneOptions = {}):
        """
        Associate a 'has_one' relationship.

        :param other: The other resource to associate with.
        :type other: str
        :param options: Additional options for the association.
        :type options: HasOneOptions
        """
        other = inflection.underscore(other)
        has_one_name = options.get("has_one_name", other)

        has_one_path = f"{cls.path}/:{cls.uid}/{has_one_name}"
        has_one_path = options.get("has_one_path", has_one_path)

        has_one_endpoint = urljoin(cls.url, has_one_path)

        def fget(self):
            endpoint = interpolate(has_one_endpoint, **self)
            response = self.session.get(endpoint)
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
    """
    Represents a 'has_many' association.

    :cvar has_many: The 'has_many' relationship definition.
    :cvar has_many_name: The name of the associated resource.
    :cvar has_many_path: The path to the associated resource.
    """

    has_many: Union[str, set[str], dict[str, HasManyOptions]]
    has_many_name: str
    has_many_path: str

    def __init__(self, **kwargs) -> None:
        """
        Initialize the 'has_many' association.
        """
        super().__init__(**kwargs)
        if hasattr(self, "has_many"):
            has_many = getattr(self, "has_many")
            self._associate(has_many, self.__associate)

    def __associate(self, other: str, options: HasManyOptions = {}):
        """
        Associate a 'has_many' relationship.

        :param other: The other resource to associate with.
        :type other: str
        :param options: Additional options for the association.
        :type options: HasManyOptions
        """

        other = inflection.underscore(other)
        other_plural = inflection.pluralize(other)
        has_many_name = options.get("has_many_name", other_plural)

        has_many_path = f"{self.path}/:{self.uid}/{has_many_name}"
        print(has_many_path)
        has_many_path = options.get("has_many_path", has_many_path)
        has_many_path = interpolate(has_many_path, **self)

        association_name = inflection.camelize(self.name + "_" + has_many_name)
        Association = resolve(other)
        bases = Association.__bases__ if Association else (Active,)
        Association = type(
            association_name,
            bases,
            {
                **vars(Association),
                "url": self.url,
                "session": self.session,
                "name": has_many_name,
                "path": has_many_path,
            },
        )

        setattr(self, has_many_name, Association)


class ActiveAssociation(BelongsToAssociation, HasOneAssociation, HasManyAssociation):
    """
    Combines all association types (belongs_to, has_one, has_many) into a single class.
    """

    pass


class Active(ActiveAssociation, ActiveBase):
    """
    Base class for all Active Record-like models.

    :cvar endpoint: The full URL endpoint for the resource.
    """

    endpoint: str  # the url and path

    def __init_subclass__(
        cls, url: Optional[str] = None, session: Optional[Session] = None, **kwargs
    ):
        """
        Automatically set up the class with a URL and session when subclassing.

        :param url: The base URL for the class.
        :type url: Optional[str]
        :param session: The session used for HTTP requests.
        :type session: Optional[Session]
        """
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

        # Ensure the base attributes are set before calling super().__init_subclass__()
        # This guarantees that these attributes are derived from this class rather than the base class.
        super().__init_subclass__(**kwargs)

        if not hasattr(cls, "endpoint"):
            endpoint = urljoin(cls.url, cls.path)
            setattr(cls, "endpoint", endpoint)

    @classmethod
    def all(cls: type[T]) -> list[T]:
        """
        Retrieve all resources from the API.

        :return: A list of instances of the class.
        :rtype: list[T]
        """
        response = cls.session.get(cls.endpoint)
        response.raise_for_status()
        body = response.json()
        return [cls(**kwargs) for kwargs in body]

    @classmethod
    def create(cls: type[T], **kwargs) -> T:
        """
        Create a new resource in the API.

        :param kwargs: The attributes to set on the resource.
        :return: An instance of the created resource.
        :rtype: T
        """
        response = cls.session.post(cls.endpoint, json=kwargs)
        response.raise_for_status()
        body = response.json()
        return cls(**body)

    @classmethod
    def find(cls: type[T], uid: str) -> T:
        """
        Find a resource by its unique identifier.

        :param uid: The unique identifier of the resource.
        :type uid: str
        :return: An instance of the found resource.
        :rtype: T
        """
        endpoint = f"{cls.endpoint}/{uid}"
        response = cls.session.get(endpoint)
        response.raise_for_status()
        body = response.json()
        return cls(**body)

    @classmethod
    def find_by(cls: type[T], **conditions) -> Optional[T]:
        """
        Find the first resource that matches the given conditions.

        :param conditions: The conditions to filter the resources.
        :type conditions: dict
        :return: The first matching resource, or None if not found.
        :rtype: Optional[T]
        """
        return next(iter(cls.where(**conditions)), None)

    @classmethod
    def first(cls: type[T]) -> Optional[T]:
        """
        Retrieve the first resource from the API.

        :return: The first resource, or None if the collection is empty.
        :rtype: Optional[T]
        """
        return next(iter(cls.all()), None)

    @classmethod
    def second(cls: type[T]) -> Optional[T]:
        """
        Retrieve the second resource from the API.

        :return: The second resource, or None if the collection has fewer than two elements.
        :rtype: Optional[T]
        """
        return next(iter(cls.all()[1:]), None)

    @classmethod
    def third(cls: type[T]) -> Optional[T]:
        """
        Retrieve the third resource from the API.

        :return: The third resource, or None if the collection has fewer than three elements.
        :rtype: Optional[T]
        """
        return next(iter(cls.all()[2:]), None)

    @classmethod
    def fourth(cls: type[T]) -> Optional[T]:
        """
        Retrieve the fourth resource from the API.

        :return: The fourth resource, or None if the collection has fewer than four elements.
        :rtype: Optional[T]
        """
        return next(iter(cls.all()[3:]), None)

    @classmethod
    def fifth(cls: type[T]) -> Optional[T]:
        """
        Retrieve the fifth resource from the API.

        :return: The fifth resource, or None if the collection has fewer than five elements.
        :rtype: Optional[T]
        """
        return next(iter(cls.all()[4:]), None)

    @classmethod
    def forty_two(cls: type[T]) -> Optional[T]:
        """
        Retrieve the forty-second resource from the API.

        :return: The forty-second resource, or None if the collection has fewer than forty-two elements.
        :rtype: Optional[T]
        """
        return next(iter(cls.all()[41:]), None)

    @classmethod
    def where(cls: type[T], **conditions) -> list[T]:
        """
        Retrieve resources that match the given conditions.

        :param conditions: The conditions to filter the resources.
        :type conditions: dict
        :return: A list of matching resources.
        :rtype: list[T]
        """
        response = cls.session.get(cls.endpoint, params=conditions)
        body = response.json()
        return [cls(**kwargs) for kwargs in body]

    def destroy(self) -> None:
        """
        Destroy the resource in the API.
        """
        endpoint = f"{self.endpoint}/:{self.uid}"
        endpoint = interpolate(endpoint, **self)
        response = self.session.delete(endpoint)
        response.raise_for_status()

    def save(self) -> None:
        """
        Save the resource to the API.
        """
        endpoint = f"{self.endpoint}/:{self.uid}"
        endpoint = interpolate(endpoint, **self)
        response = self.session.put(endpoint, json=self)
        response.raise_for_status()

    def update(self, **kwargs) -> None:
        """
        Update the resource with the given attributes and save it.

        :param kwargs: The attributes to update.
        """
        super().update(**kwargs)
        self.save()
