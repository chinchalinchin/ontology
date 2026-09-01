# Ontology: Emergence

TODO

## Towns

Every Sprite has a Community Radius, `mutator.parameter.community.radius`. When more than 2 Sprites own `sprite.memory.property` within their respective Community Radii, a Town Charter is formed.

To visualize the process, imagine A, B, C represent the circles implied by the Community Radius of 3 Sprites, each centeedr on the location of their respective Property (assuming each Sprite only owns one piece of Property). For any A, B, C, where A and B overlap, B and C overlap, but not necessarily A and C, the conditions for a Town Charter are satisfied.

Any time a Charter is formed, a `town-hall` Strut is instantiated in the center of A, B, C. If the center is otherwise occupied, the `town-hall` Position is randomly generated within the Community Radii.

**CharterConfiguration**

- `collection: int`: Number of ticks per tax collection.

**CharterState**

- `name: str`
- `radius: int`:
- `mayor: str`:
- `taxes`:
    - `property`: float
    - `excise`: float
- `property: Dict[str, Position]`
- `coffers: int`
- `citizens: List[str]`

### Government

**Elections**

TODO

**Mayor**

Once a mayor is elected and assigned to the Charter, the `charter.coffers` become bound to that Sprite's `wallet`, effectively giving them access to the [Tax Income](#taxes).

### Taxes

A Charter enforces two kinds of taxes within its boundaries: Excise and Property.

**Property Taxes**

While a Charter is in effect, any Sprite who owns Property within the Charter Radius is charged a Property tax periodically. The amount of the Property Tax is deducted from the Sprite `wallet` and added to `charter.coffers`.

If a Sprite's `wallet < property_tax` when the taxes come due, the Property is confiscated by the Charter and assigned an owner of `charter.name`.

The Property tax deducted by a Charter for a given Sprite who owns Property within that Charter is calculated as follows:

$$
\text{Property Tax} = \frac{\text{total value of Sprite Struts}}{\text{total value of Charter Struts}} \cdot \text{Charter Property Tax Rate} \cdot \text{total value of Sprite Struts}
$$

**Excise Taxes**

Any time a transaction occurs within `charter.radius` of `town-hall`, an `excise` tax percentage is applied and added to `charter.coffers`.