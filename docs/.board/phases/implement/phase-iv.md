#### Phase IV: Mechanics

##### Commerce, Communication and Prices

1. Subjective Value and "Gossip" Pricing

To avoid a global price board, prices must be decentralized. A Sprite should only know what *it* thinks an item is worth, and what it recently heard from others.

* **Subjective Valuation:** A Sprite's base valuation of an item is a function of its `Inventory` and its `Goal`. If a Sprite's overarching `Goal` requires 50 Wood (to build a house), and it has 0 Wood, its internal valuation for Wood is extremely high. Once it has 45 Wood, the urgency drops.
* **Price Memory:** Add a `price_book: Dict[str, float]` to the `Memory` state model. This tracks the Sprite's belief of what things cost.
* **Price Transmission (Gossip):** You already have a `speak` INtention and a `memory.communications` buffer. When two Sprites enter the `speak` Intention within a certain radius, the `CommunicationMechanic` doesn't just swap dialogue; it swaps the latest transaction values from their `price_book`.

If Wood is scarce in the NPC town, Sprites there will continuously bid up the price in their local `price_books`. When an NPC travels to the Borderlands and `communicates` with an Enemy, the Enemy's `price_book` updates with this high Wood price, incentivizing the Enemy to gather Wood and bring it to the NPC town to sell.

2. The `barter` Intention & Transactions


* **The Intent:** A Sprite realizes it needs Wood. Its Intentionn matrix evaluates its inventory, transitioning it from `idle` -> `find` (Goal: Sprite with Wood). Once within `parameters.vision.radius` of a target Sprite, it transitions to `barter`.
* **The CommerceMechanic:** Add a `CommerceMechanic` to `Board.play()`. This mechanic specifically queries `board.sprites` for Sprites in the `barter` Intention.
* **The Handshake:**
    - Sprite A enters `barter` with target Sprite B.
    - Sprite B's Intention matrix evaluates the interaction. If Sprite B feels safe and is interested, it also transitions to `barter`.
    - The `CommerceMechanic` checks if their subjective values overlap. If Sprite A is willing to pay 10 Gold for Wood, and Sprite B is willing to sell it for 8 Gold, a transaction occurs.
    - The mechanic directly deducts/adds to their respective `inventory.loot` and `inventory.wallet`, and updates both of their `price_books` to 9 Gold (the clearing price).
    - The Intention transitions to `return` or `idle`.

3. Congregation and Property (Town Formation)

Towns shouldn't be predefined zones. A "town" should simply emerge as a spatial cluster of "Owned Assets" bounded by the geography of the `Board`.

* **The `build` Intention:** When a Sprite acquires enough materials (e.g., 50 Wood, 10 Stone), its overarching `Goal` shifts. Its Intention changes to `wander` to find an empty plot (using `CollisionMechanics` to ensure the space is clear), and then enters a `build` Intention.
* **Asset Spawning:** While in the `build` Intention, a new `Mutable, Inanimate Asset` (e.g., `Foundation`) is appended to the `Board`. As the game loop progresses, the Sprite consumes its inventory, and the `AnimationMechanics` advances the `Foundation`'s frame until it becomes a `House`.
* **Property Ownership:** The `House` Asset's `State` contains an `owner_name` matching the Sprite.
* **Congregation (The "Gravity" of Towns):** Why do NPCs group together? Modify your `Motivations` (e.g., `kinship`, `safety`). A Sprite with `safety` motivation will set a `Goal` to pathfind toward the highest density of Assets owned by its own category (NPCs). Enemies might have a `profit` motivation, pathfinding toward resource-rich terrain (mines/forests) and building their homes there. The "Borderlands" town naturally emerges in the spatial midpoint between the resource-rich Enemy town and the safe NPC town, because traders want to minimize travel distance.

4. Emergent Conflict: Scarcity -> Violence

```yaml
  barter:
    # If the transaction is successful, go back to idle
    - next: idle
      condition:
        - sprite.inventory.wallet > 0

    # THE ESCALATION TRIGGER:
    # If the target wants too much money, or won't trade, but I need the item for survival
    - next: threaten
      condition:
        - sprite.memory.goal.target.category == 'sprite'
        - sprite.inventory.wallet < sprite.price_book['wood']
        - sprite.psyche.motivation == 'survival'
          
  threaten:
    # If the target submits and drops the loot, return to idle
    - next: idle
      condition:
        - not sprites[sprite.memory.goal.name].inventory.loot['wood']
        
    # If the target doesn't submit, escalate to attack
    - next: attack
      condition:
        - sprites[sprite.memory.goal.name].intention != 'escape'

```

**The Emergent Narrative:**

1. The NPC town exhausts its local forest.
2. The NPC travels to the Borderlands to buy Wood from the Enemies.
3. The Enemies have realized Wood is in high demand (via the gossip network updating their `price_book`), so they refuse to sell it for cheap.
4. The NPC doesn't have enough Gold in its `wallet`.
5. The `CommerceMechanic` refuses the trade.
6. The NPC's Intention matrix sees that it cannot afford the Wood, but its `motivation` is `survival`. The matrix kicks the NPC into `threaten`.
7. The Enemy, having a `profit` motivation and a high `strength` character stat, refuses to drop the Wood and enters `recoil` -> `attack`.
8. Violence erupts. Other Sprites nearby with `kinship` motivations see their ally in `attack` Imtention and cascade into the fight. A full-scale border war emerges purely from inflation.

### Architectural Updates Required

To support this phase of the engine, 

1. **YAML Schemas:** Add `price_book: Dict[str, float]` to `PyMemoryState`.
2. **Cython Mechanics:** Create a `CommerceMechanic` that processes interactions between overlapping Sprites in the `barter` state.
3. **Spawning Logic:** Create a mechanism in the `Board` class to dynamically instantiate and append new `Object` Assets (like Houses) to the `assets` list at runtime when a Sprite is in the `build` Extension.
4. **Spatial Hashing:** If Sprites are constantly querying "where is the nearest cluster of friendly houses" or "who has Wood," your Cython `math.pyx` will need a spatial hashing grid. Checking the distance to every other Sprite/House in a $O(N^2)$ loop will crush your framerate as towns grow large.