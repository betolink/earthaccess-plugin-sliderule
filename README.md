# earthaccess-sliderule

On-demand ICESat-2 and GEDI processing with
[SlideRule](https://slideruleearth.io/), via the earthaccess plugin contract.

```python
import earthaccess

results = earthaccess.search_data(short_name="ATL06", ...)

plugin = earthaccess.plugins.sliderule
plugin.configure(url="https://slideruleearth.io", organization="my-org")

df = plugin.run(
    results,
    api="atl06p",
    parms={"pass_invalid": False},
)
```

## Contract

- `output = "dataframe"`, `auth = "own"` (SlideRule manages its own
  credentials), `requires_results = False` (runs from `aoi` + `parms` alone).
- `needs = {"native_id"}`: searched granules scope the call unless `resources`
  is passed explicitly.
- The client keeps global state, so calls are serialized with a lock and
  `init()` runs once, inside the worker.

## Verification points

`src/earthaccess_sliderule/plugin.py` isolates the unverified `sliderule.init`
keywords and `run()` signature (in particular whether `resources` is a keyword
or lives in `parms`).

## License

MIT.
