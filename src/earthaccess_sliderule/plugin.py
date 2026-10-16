"""The SlideRule plugin: on-demand processing with its own credentials.

SlideRule manages its own authentication, so this plugin never touches
``ctx.auth``. The client keeps global state, so every call is serialized with a
lock and ``init`` runs once, inside the worker.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any

from earthaccess_plugin_spec import PluginBase

__all__ = ["SlideRulePlugin"]


class SlideRulePlugin(PluginBase):
    name = "sliderule"
    needs = frozenset({"native_id"})
    requires_results = False  # can run from aoi + parms alone
    auth = "own"  # SlideRule manages its own credentials
    output = "dataframe"

    @dataclass
    class Options:
        api: str  # required, for example 'atl06p'
        parms: dict = field(default_factory=dict)
        aoi: dict | None = None
        resources: list[str] | None = None  # overrides results.native_ids

    def __init__(self, ctx: Any) -> None:
        super().__init__(ctx)
        self._init_kwargs: dict[str, Any] = {}
        self._ready = False
        self._lock = threading.Lock()

    def configure(self, **init_kwargs: Any) -> None:
        """Set ``sliderule.init`` keyword arguments (url, organization, ...)."""

        self._init_kwargs = init_kwargs
        self._ready = False

    def _request(self, results: Any, options: Options) -> Any:
        resources = options.resources
        if resources is None and results is not None:
            resources = list(results.native_ids)

        def call() -> Any:
            import sliderule

            with self._lock:
                if not self._ready:
                    sliderule.init(**self._init_kwargs)
                    self._ready = True
                # VERIFY: run() signature (resources as an argument or in parms).
                return sliderule.run(
                    options.api, options.parms, aoi=options.aoi, resources=resources
                )

        return self.job(call)
