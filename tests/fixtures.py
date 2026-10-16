"""Conformance fixtures for SlideRule: a fake ``sliderule`` module."""

from __future__ import annotations

import sys
import types
from contextlib import AbstractContextManager
from typing import Any
from unittest import mock

from earthaccess_plugin_spec.results import GranuleResultSet
from earthaccess_plugin_spec.testing import Fixtures

__all__ = ["FakeSlideRule", "SlideRuleFixtures", "make_granule"]


def make_granule(
    *,
    collection_id: str = "C-ATL06",
    concept_id: str = "G1",
    ur: str = "G1.EXAMPLE",
    short_name: str = "ATL06",
    version: str = "006",
) -> dict[str, Any]:
    return {
        "meta": {"concept-id": concept_id, "collection-concept-id": collection_id},
        "umm": {
            "GranuleUR": ur,
            "CollectionReference": {"ShortName": short_name, "Version": version},
        },
    }


class FakeSlideRule:
    """Stand-in for the global-state ``sliderule`` module."""

    def __init__(self) -> None:
        self.inits: list[dict[str, Any]] = []
        self.runs: list[dict[str, Any]] = []

    def init(self, **kwargs: Any) -> None:
        self.inits.append(kwargs)

    def run(
        self,
        api: str,
        parms: dict[str, Any],
        aoi: dict | None = None,
        resources: list[str] | None = None,
    ) -> dict[str, Any]:
        self.runs.append(
            {"api": api, "parms": parms, "aoi": aoi, "resources": resources}
        )
        return {"api": api, "count": len(resources or [])}


def _module_for(backend: FakeSlideRule) -> types.ModuleType:
    module = types.ModuleType("sliderule")
    module.init = backend.init  # type: ignore[attr-defined]
    module.run = backend.run  # type: ignore[attr-defined]
    return module


class SlideRuleFixtures(Fixtures):
    def __init__(self, backend: FakeSlideRule | None = None, **kwargs: Any) -> None:
        kwargs.setdefault(
            "options",
            {
                "api": "atl06p",
                "parms": {"pass_invalid": False},
                "aoi": {"type": "FeatureCollection", "features": []},
            },
        )
        kwargs.setdefault(
            "result_set", GranuleResultSet([make_granule(collection_id="C-ATL06")])
        )
        kwargs.setdefault(
            "unsupported_result_set",
            GranuleResultSet(
                [
                    make_granule(
                        collection_id="C-LANDSAT",
                        short_name="LANDSAT_8_C1",
                    )
                ]
            ),
        )
        super().__init__(**kwargs)
        self.backend_impl = backend or FakeSlideRule()

    def backend(self) -> AbstractContextManager[Any]:
        return mock.patch.dict(
            sys.modules, {"sliderule": _module_for(self.backend_impl)}
        )
