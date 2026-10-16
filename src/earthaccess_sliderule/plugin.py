"""The SlideRule plugin: on-demand processing with its own credentials.

SlideRule manages its own authentication, so this plugin never touches
``ctx.auth``. The client keeps global state, so every call is serialized with a
lock and ``init`` runs once, inside the worker.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any

from earthaccess_plugin_spec import PluginBase, Support

__all__ = ["SlideRulePlugin"]

# The allowlist is authoritative, so a miss is a hard no. VERIFY against
# SlideRule's docs, including whether a version is needed as well.
_SUPPORTED_SHORT_NAMES = frozenset(
    {
        # ICESat-2
        "ATL03",
        "ATL06",
        "ATL08",
        "ATL09",
        "ATL13",
        "ATL24",
        # GEDI
        "GEDI01_B",
        "GEDI02_A",
        "GEDI02_B",
        "GEDI04_A",
        "GEDI_L2A",
        "GEDI_L4A",
    }
)


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

    def _supports(self, results: Any) -> Support:
        short_name = (getattr(results, "short_name", "") or "").upper()
        if short_name in _SUPPORTED_SHORT_NAMES:
            return Support(True)
        label = short_name or results.collection_id
        return Support(False, f"{label} is not a SlideRule dataset")
