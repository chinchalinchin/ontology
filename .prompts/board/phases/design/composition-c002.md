#### Design: Composition C002 - Regalia Galleria

- **Purpose**: An art gallery to contain various Asset tests.
- **Description**: An ornate exterior. The interior should be a long hallway with doors on either side. Each door will lead to a separate "art installation" room. There should be eight rooms in total. If a room does not have a description below, leave it empty for future tests, but ensure it has walls and surfaces and can be traversed.

##### Composition: Model

```yaml
# TODO
```

##### Composition: Tasks

* `[x]` **Exterior**: Symmetrical $384 \times 288$ palace facade featuring `wall-palace` masonry, `skylight-iron-octagon` crown, four `pillar-stone-corinthian` columns, arched glass windows, wall torches, a granite-and-gold-carpet forecourt plaza, a `birdbath`, an exterior directory `bulletin` sign, and a central `door-double` entrance.
* `[x]` **Hallway (`galleria-hallway`)**: A $768 \times 288$ central concourse paved with 24 `support-granite-border` slabs and a central `carpet-cotton-gold-border` runner, divided into bays by `pillar-marble` columns, connecting 4 North-Wing exhibition doors (`door-mansion`), 4 South-Wing exhibition doors (`door-shadow`), and the central `door-shadow-double` foyer exit.
* `[x]` **Room 1 — The Hall of Reactions (`galleria-room-reactions`)**: $384 \times 288$ hall featuring two `spinning-dummy` Reactables on an exhibition rug with open floor area in the eastern bay for future attractions.
* `[x]` **Room 2 — The Hall of Elevations (`galleria-room-elevations`)**: $480 \times 416$ hall featuring a contiguous $384\text{ px}$ elevated promenade across all four `Platform` orders (`platform-stone-doric`, `platform-stone-ionic`, `platform-stone-corinthian`, `platform-stone`) at `elevation = 1`, flanked by ascending/descending `steps-stone` (`direction: up`) and a second-tier lateral `steps-stone` (`direction: left`, `elevation: 1`) leading to an upper `elevation = 2` `platform-stone-corinthian` terrace.
* `[x]` **Room 3 — The Hall of Passivity (`galleria-room-passivity`)**: $384 \times 288$ hall showcasing `continuous` (`grandfather-clock`, `torch`) and `periodic` (`birdbath`) Passive Effects around a `carpet-cotton-palace` centerpiece.
* `[x]` **Room 4 — The Hall of Vanity (`galleria-room-vanity`)**: $384 \times 288$ hall exhibiting all `Purpose: Decor` partitions—wall-anchored `curtains-red` and paintings (`painting-portrait-king`, `painting-portrait-queen`, `painting-abstract`, `painting-cityscape`, `painting-sailboat`), `fixture-fireplace`, `fixture-vanity`, `shelf-cabinet`, `table-hallway-candlesticks`, and `table-dinner-round`.
* `[x]` **Room 5 — The Hall of Study (`galleria-room-study`)**: $384 \times 288$ hall housing six `Sign` instances (`bulletin`, `poster`, `chalkboard`, `post`, `bevel`, `headstone`) bound to seasonal Library personas.
* `[x]` **Rooms 6, 7 & 8 — Exhibition Annexes I–III (`galleria-room-annex-west`, `galleria-room-annex-center`, `galleria-room-annex-east`)**: Three $384 \times 288$ walled, wood-floored, fully traversable exhibition halls reserved for future asset tests.
