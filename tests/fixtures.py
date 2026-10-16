"""Conformance fixtures for SlideRule: a fake ``sliderule`` module."""

from __future__ import annotations

import sys
import types
from contextlib import AbstractContextManager
from typing import Any
from unittest import mock

from earthaccess_plugin_spec.testing import Fixtures

__all__ = ["FakeSlideRule", "SlideRuleFixtures"]


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
        super().__init__(**kwargs)
        self.backend_impl = backend or FakeSlideRule()

    def backend(self) -> AbstractContextManager[Any]:
        return mock.patch.dict(sys.modules, {"sliderule": _module_for(self.backend_impl)})
