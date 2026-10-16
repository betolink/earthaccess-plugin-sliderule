import pytest
from earthaccess_plugin_spec import Support, UnsupportedCollectionError
from earthaccess_plugin_spec.results import GranuleResultSet
from earthaccess_plugin_spec.testing import fake_context, sample_result_set

from earthaccess_sliderule import SlideRulePlugin

from .fixtures import FakeSlideRule, SlideRuleFixtures, make_granule


class TestOptions:
    def test_api_required(self):
        with pytest.raises(TypeError):
            SlideRulePlugin.Options()


class TestRequest:
    def test_resources_from_results(self):
        backend = FakeSlideRule()
        fixtures = SlideRuleFixtures(backend=backend)
        plugin = SlideRulePlugin(fake_context())
        with fixtures.backend():
            result = plugin.run(fixtures.result_set, **fixtures.options)
        assert result["count"] == 1
        assert backend.runs[0]["resources"] == list(fixtures.result_set.native_ids)
        assert backend.runs[0]["api"] == "atl06p"

    def test_resources_override(self):
        backend = FakeSlideRule()
        fixtures = SlideRuleFixtures(backend=backend)
        plugin = SlideRulePlugin(fake_context())
        with fixtures.backend():
            plugin.run(
                fixtures.result_set,
                api="atl06p",
                parms={},
                resources=["custom-1", "custom-2"],
            )
        assert backend.runs[0]["resources"] == ["custom-1", "custom-2"]

    def test_requires_no_results(self):
        backend = FakeSlideRule()
        fixtures = SlideRuleFixtures(backend=backend)
        plugin = SlideRulePlugin(fake_context())
        with fixtures.backend():
            result = plugin.run(
                None, api="atl06p", parms={}, aoi={"type": "Point", "coordinates": [0, 0]}
            )
        assert result["count"] == 0
        assert backend.runs[0]["resources"] is None

    def test_init_runs_once(self):
        backend = FakeSlideRule()
        fixtures = SlideRuleFixtures(backend=backend)
        plugin = SlideRulePlugin(fake_context())
        plugin.configure(url="https://sliderule.example", organization="org")
        with fixtures.backend():
            plugin.run(fixtures.result_set, **fixtures.options)
            plugin.run(fixtures.result_set, **fixtures.options)
        assert backend.inits == [
            {"url": "https://sliderule.example", "organization": "org"}
        ]
        assert len(backend.runs) == 2

    def test_configure_resets_readiness(self):
        backend = FakeSlideRule()
        fixtures = SlideRuleFixtures(backend=backend)
        plugin = SlideRulePlugin(fake_context())
        with fixtures.backend():
            plugin.run(fixtures.result_set, **fixtures.options)
            plugin.configure(url="https://other.example")
            plugin.run(fixtures.result_set, **fixtures.options)
        assert len(backend.inits) == 2


def test_entry_point_registered():
    from importlib.metadata import entry_points

    names = {ep.name for ep in entry_points(group="earthaccess.plugins")}
    assert "sliderule" in names


def test_sample_result_set_has_native_ids():
    assert sample_result_set().native_ids


class TestSupport:
    @pytest.mark.parametrize("short_name", ["ATL06", "atl06", "GEDI02_A"])
    def test_allowlisted(self, short_name):
        plugin = SlideRulePlugin(fake_context())
        results = GranuleResultSet([make_granule(short_name=short_name)])
        assert plugin.supports(results) == Support(True)

    def test_rejects_landsat(self):
        plugin = SlideRulePlugin(fake_context())
        results = GranuleResultSet(
            [make_granule(collection_id="C-LANDSAT", short_name="LANDSAT_8_C1")]
        )
        support = plugin.supports(results)
        assert support.ok is False
        assert "LANDSAT_8_C1" in support.reason

    def test_request_raises_before_backend(self):
        backend = FakeSlideRule()
        fixtures = SlideRuleFixtures(backend=backend)
        plugin = SlideRulePlugin(fake_context())
        results = GranuleResultSet(
            [make_granule(collection_id="C-LANDSAT", short_name="LANDSAT_8_C1")]
        )
        with fixtures.backend(), pytest.raises(UnsupportedCollectionError):
            plugin.request(results, api="atl06p")
        assert backend.runs == []
