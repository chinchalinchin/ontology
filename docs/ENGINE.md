# Engine

The engine module contains the guts of the game world: all of the calculations that go into its physics, the decision tree generation for its sprites, and the statistical learning module for sprite state guessing.

## Calculator

## Collisions

## Paths

## Dialogue

## Scripts

## Learning

(<sup><sub>This component of the engine is near and dear to my heart.</sub></sup>)

THe _Learning_ module methods consume the world state information and its results are applied to the _Sprite_\s' state information. Rudimentary statistically learning is applied using the sprite states as a predictor variable matrix and the hero state as a response variable. Predictions are used to inform sprite "guesses" about what is going to happen in the next world iteration.

### Anaylsis

### Storage