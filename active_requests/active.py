import importlib
import inspect
from typing import Generic, Optional, TypeVar, Union
from urllib.parse import urljoin
from requests import Session

R = TypeVar("R", bound="Active", covariant=True)

class HasOneAssociation:
    has_one: Union[str | type["Active"]]
    has_one_path: str

    def __init_subclass__(cls: type["HasOneAssociation"]) -> None:
        if hasattr(cls, "has_one"):
            cls.has_one = cls.resolve_has_one()

            if not hasattr(cls, "has_one_path"):
                cls.has_one_path = cls.has_one.path

    @classmethod
    def resolve_has_one(cls: type["Active"]) -> type["Active"]:
        has_one = getattr(cls, 'has_one')
        if isinstance(has_one, str):
            print(has_one)
            resolved_type = cls.resolve_class(has_one)

            if not resolved_type:
                raise ValueError(
                    f"has_one reference '{has_one}' could not be resolved in globals()."
                )

            if not isinstance(resolved_type, type):
                raise ValueError(
                    f"has_one reference '{has_one}' resolved to '{resolved_type}', which is not a type."
                )

            if not issubclass(resolved_type, Active):
                raise ValueError(
                    f"has_one reference '{has_one}' resolved to '{resolved_type}', which is not a subclass of Active."
                )

            return resolved_type

        elif isinstance(has_one, type):
            if not issubclass(has_one, Active):
                raise ValueError(
                    f"has_one type '{has_one}' is not a subclass of Active."
                )

            return has_one

        else:
            raise TypeError(
                "has_one must be a string referencing a subclass of Active or a type that is a subclass of Active."
            )


class Association(BelongsToAssociation, HasOneAssociation):
    pass


class Active(Generic[R], dict, Association):
    name: str  # the class name in lowercase
    path: str  # the plural name; represents the resource collection name
    endpoint: str  # the url and path

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
    def create(cls: type[R], **kwargs) -> R:
        response = cls.session.post(cls.endpoint, json=kwargs)
        response.raise_for_status()
        body = response.json()
        return cls(**body)

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

    @classmethod
    def resolve_class(cls, class_name: str):
        # Get the calling module's name from the call stack
        stack = inspect.stack()
        caller_frame = stack[1]
        module = inspect.getmodule(caller_frame[0])

        if module is None:
            raise ImportError("Could not determine the calling module.")

        module_name = module.__name__

        try:
            # Dynamically import the module using the resolved module_name
            module = importlib.import_module(module_name)
            # Retrieve the class from the imported module
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            raise ImportError(
                f"Could not resolve class {class_name} from module {module_name}: {e}"
            )
