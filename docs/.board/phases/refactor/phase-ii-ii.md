#### Refactor: Phase II - Registry Indexing

The Registry should be completely agnostic to the concept of Tiles, Sprites, or Widgets. Its only responsibility should be managing memory (`TexturePtr`) and holding a map of `string_key -> (src_x, src_y, w, l)`.

To achieve this, the responsibility of calculating crop maps must be pushed down to the `Frame` objects. The `Registry` will iterate over the configurations, fetch the appropriate `Frame` behavior from the `Factory`, and ask the `Frame` object to return its pre-calculated index map based on its properties.

**Task 1: Expand the `Frame` Interface**

* [x] Update the abstract `Frame` base class in `app.assets.base`.
* [x] Introduce a new static or class method (e.g., `index(id, properties, recipe)`).
* [x] This method must return a dictionary mapping all possible string keys for an asset to their corresponding crop coordinates: `dict[str, tuple[int, int, int, int]]`.

**Task 2: Implement Component Indexing Logic**

* [x] Move the specific indexing logic out of `Registry._index()` and into the respective frame behaviors in `app.assets.frames`:
* [x] **`SingleFrame`**: Return a 1:1 mapping of the ID to the full dimensions.
* [x] **`IterableFrame`**: Ingest the `AnimationRecipe` (Binary vs. Persistent/Temporary) to determine if it should index by `id-0`/`id-1` or iterate through `count` to generate a sequential horizontal strip of coordinates.
* [x] **`StateFrame`**: Ingest the `actions` and `directions` properties to generate the full `id-action-direction-frame` matrix of coordinates.

**Task 3: Refactor `Registry._index()`**

* [x] Strip out all `if/elif` category and recipe checks.
* [x] Update the loop to retrieve the assigned `FrameRecipe` for the current instance.
* [x] Invoke `Factory.frame(recipe)` to get the worker class, call its new generation method with the parsed properties, and update `self._frames` with the resulting dictionary.

**Task 4: Data-Driven Texture Assembly (`Registry._assemble()`)**

* [x] Remove the explicit checks for `PIXIES` and `SPRITES`.
* [x] Update the loop to scan all ingested property dictionaries. If an object possesses a `stack` attribute (or a `personas` dictionary containing stacks), trigger the `render.compose()` logic.
    * This ensures any future asset type can utilize Cython-hardware texture stacking simply by defining it in the YAML schema.