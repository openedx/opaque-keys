# keys.py 
import typing as t
from dataclasses import dataclass


# Abstract abstract base keys

@dataclass(frozen=True)
class ParsableKey:
    def from_string(self, key_string: str) -> t.Self:
        raise NotImplementedError

@dataclass(frozen=True)
class PluggableKey(ParsableKey):
    @property
    def prefix(self) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class ContextKey(PluggableKey):
    pass

@dataclass(frozen=True)
class UsageKey(PluggableKey):
    def context_key(self) -> ContextKey:
        raise NotImplementedError


# Abstract base keys for Packages and the things in them.
# Not tied to Libraries.

@dataclass(frozen=True)
class PackageKey(ParsableKey):
    pass

@dataclass(frozen=True)
class CollectionKey(ParsableKey):
    @property
    def package_key(self) -> PackageKey:
        raise NotImplementedError
    @property
    def collection_code(self) -> str:
        raise NotImplementedError

@dataclass(frozen=True)
class EntityKey(ParsableKey):
    @property
    def package_key(self) -> PackageKey:
        raise NotImplementedError
    @property
    def type_code(self) -> str:
        raise NotImplementedError
    @property
    def entity_code(self) -> str:
        raise NotImplementedError

@dataclass(frozen=True)
class ComponentKey(EntityKey):
    type_namespace: str
    type_name: str
    @property
    def type_code(self):
        return f"{self.type_name}:{self.type_namsepace}"

@dataclass(frozen=True)
class ContainerKey(EntityKey):
    pass


# Concrete keys for Libraries and the things in them.
@dataclass(frozen=True)
class LibraryKey(PackageKey, ContextKey):
    """lib:{org}:{library_code}"""
    prefix: t.ClassVar[str] = "lib"
    org: str
    library_code: str

# (Abstract)
@dataclass(frozen=True)
class LibraryEntityKey(EntityKey):
    library_key: LibraryKey
    @property
    def package_key(self) -> PackageKey:
        return self.library_key 

class LibraryCollectionKey(CollectionKey):
    """lib-collection:{library_key.org}:{library_key.library_code}:{collection_code}"""
    prefix: t.ClassVar[str] = "lib-collection"
    library_key: LibraryKey
    collection_code: str

class LibraryComponentKey(LibraryEntityKey, ComponentKey):
    """lb:{library_key.org}:{library_key.library_code}:{type_namespace}:{type_name}:{entity_code}"""
    prefix: t.ClassVar[str] = "lb"
    pass

class LibraryContainerKey(LibraryEntityKey, ContainerKey): 
    """lct:{library_key.org}:{library_key.library_code}:{type_code}:{container_code}"""
    prefix: t.ClassVar[str] = "lct"
    pass

# Context&Usage versions of Library keys so that we can preview items in the authoring environment
class LibraryPreviewContextKey(LibraryKey, ContextKey):
    pass
class LibraryPreviewUsageKey(LibraryEntityKey, ContextKey)
    pass