"""Persistent per-material values for dynamically described MadMapper inputs.

The store is intentionally independent of TouchDesigner.  A UI may rebuild a
material schema after import/source edits and merge it here: values survive
when name and type are unchanged, while new or type-changed inputs receive the
new material default.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from pixelblaze_mapper.madmapper_parameters import (
    MaterialParameter,
    coerce_value,
    default_values,
    uniform_vector,
)


@dataclass
class _Entry:
    types: dict[str, str]
    values: dict[str, Any]
    page: int = 0


class ImportedMaterialStateStore:
    def __init__(self) -> None:
        self._materials: dict[str, _Entry] = {}

    @property
    def material_ids(self) -> tuple[str, ...]:
        return tuple(self._materials)

    def merge(
        self, material_id: str, schema: Iterable[MaterialParameter]
    ) -> dict[str, Any]:
        key = str(material_id).strip()
        if not key:
            raise ValueError("material_id must not be empty")
        parameters = tuple(schema)
        defaults = default_values(parameters)
        previous = self._materials.get(key)
        values: dict[str, Any] = {}
        types: dict[str, str] = {}
        for parameter in parameters:
            types[parameter.name] = parameter.kind
            if previous is not None and previous.types.get(parameter.name) == parameter.kind:
                candidate = previous.values.get(parameter.name, defaults[parameter.name])
            else:
                candidate = defaults[parameter.name]
            values[parameter.name] = coerce_value(parameter, candidate)
        self._materials[key] = _Entry(
            types=types,
            values=values,
            page=previous.page if previous is not None else 0,
        )
        return dict(values)

    def values(self, material_id: str) -> dict[str, Any]:
        return dict(self._materials[str(material_id)].values)

    def set_value(
        self,
        material_id: str,
        parameter: MaterialParameter,
        value: Any,
        *,
        component: int | None = None,
    ) -> Any:
        entry = self._materials[str(material_id)]
        current = entry.values[parameter.name]
        if component is not None:
            if not 0 <= int(component) < parameter.components:
                raise IndexError(component)
            vector = list(current) if isinstance(current, (list, tuple)) else [current]
            vector.extend([0.0] * (parameter.components - len(vector)))
            vector[int(component)] = value
            value = vector
        result = coerce_value(parameter, value)
        entry.values[parameter.name] = result
        return result

    def page(self, material_id: str, page_count: int | None = None) -> int:
        value = self._materials[str(material_id)].page
        if page_count is None:
            return value
        return max(0, min(max(0, int(page_count) - 1), value))

    def set_page(self, material_id: str, page: int, page_count: int) -> int:
        value = max(0, min(max(0, int(page_count) - 1), int(page)))
        self._materials[str(material_id)].page = value
        return value

    def uniform_vectors(
        self, material_id: str, schema: Iterable[MaterialParameter]
    ) -> dict[str, tuple[float, float, float, float]]:
        values = self._materials[str(material_id)].values
        return {
            parameter.uniform: uniform_vector(parameter, values[parameter.name])
            for parameter in schema
            if not parameter.compile_time
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": 1,
            "materials": {
                key: {"types": entry.types, "values": entry.values, "page": entry.page}
                for key, entry in self._materials.items()
            },
        }

    @classmethod
    def from_dict(cls, document: Mapping[str, Any]) -> "ImportedMaterialStateStore":
        store = cls()
        for key, raw in dict(document.get("materials", {})).items():
            if not isinstance(raw, Mapping):
                continue
            store._materials[str(key)] = _Entry(
                types={str(name): str(kind) for name, kind in dict(raw.get("types", {})).items()},
                values=dict(raw.get("values", {})),
                page=max(0, int(raw.get("page", 0))),
            )
        return store


__all__ = ["ImportedMaterialStateStore"]
