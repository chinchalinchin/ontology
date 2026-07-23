# Ontology: Plotting

Due to the nature of the Ontology game engine, a Plot is not scripted, in the sense that Sprite Actions are hardcoded and pre-determined down to the pixels. Conditions are reached to change the World state, which causes a Player's `plot-key` attribute to update. This in turn is affects what states can be reached by the gameplay loop. 

As a simple example, a Plot state might be defined to change conditional on the existence of Sprite (i.e. whether a character is alive or dead). In the first state, a Sprite might have access to a Communication in its Memory (See [Sprite documentation](./02-sprites.md) for more details on the internal mechanics of Sprites)