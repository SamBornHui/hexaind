from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Iterator, List


class DirectoryMapping(Mapping[str, "DirectoryMapping"]):

    def __init__(self, base_path: Path):
        self.base_path = base_path

    @staticmethod
    def _key_conversion(key: str) -> str:
        return key.replace(" ", "_SPACE_").replace("/", "_SLASH_")

    @staticmethod
    def _key_rconversion(rkey: str) -> str:
        return rkey.replace("_SPACE_", " ").replace("_SLASH_", "/")

    def __getitem__(self, key: str) -> DirectoryMapping:
        key = DirectoryMapping._key_conversion(key)
        if not (base_path := self.base_path / key).exists():
            raise KeyError(f"Key {key} not found")
        return DirectoryMapping(base_path)

    def get_based_on_wildcards(self, pattern: str) -> List[DirectoryMapping]:
        pattern = DirectoryMapping._key_conversion(pattern)
        matching_paths = list(self.base_path.glob(pattern))

        if not matching_paths:
            return [] #raise exception and handle in next layer

        return [DirectoryMapping(path) for path in matching_paths]


    class DirectoryMappingIterator(Iterator):

        def __init__(self, base_path: Path):
            self.iterator = base_path.iterdir()

        def __iter__(self) -> Iterator[str]:
            return self

        def __next__(self) -> str:
            base_path = next(self.iterator)
            return DirectoryMapping._key_rconversion(base_path.name)

    def __iter__(self) -> Iterator[str]:
        return DirectoryMapping.DirectoryMappingIterator(self.base_path)

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(base_path={repr(self.base_path)})"
