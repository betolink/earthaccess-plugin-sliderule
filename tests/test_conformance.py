from earthaccess_plugin_spec.testing import run_conformance

from earthaccess_sliderule import SlideRulePlugin

from .fixtures import SlideRuleFixtures


def test_conformance():
    run_conformance(SlideRulePlugin, fixtures=SlideRuleFixtures())
