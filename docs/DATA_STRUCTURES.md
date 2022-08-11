# Data Structures

## World

### Configuration

* composite_conf

```python
self.composite_conf = munch.Munch({

})
```

* sprite_statue

Ingested from _data/conf/sprites.yaml_.

```python
self.sprite_stature = munch.Munch({
    'sprite_1': {
        'state_1': state_1_frames, # int
        'state_2': state_2_frames, # int
        # ..
    },
})
```

* apparel_properties

Ingested from _data/conf/apparel.yaml_.

```python
self.apparel_properties = munch.Munch({
    'apparel_1': {
        'animate_states': [
            'state_1',
            'state_2',
            # ...
        ]
    },
    # ...
})
```

* plate_properties

Ingested from _data/conf/plates.yaml_.

```python
self.plate_properties = munch.Munch({

})
```

* strut_properties

Ingested from _data/conf/struts.yaml_

```python
self.strut_properties = munch.Munch({
    'strut_1': {
        'hitbox_1': hitbox_dim, # tuple
        # ...
    }
})
```

* sprite_properties

```python
self.sprite_properties = munch.Munch({
    'sprite_1': {
        'speed':{
            'walk': walk, # int
            'run': run # int
            'collide': collide
        }
        'size': (w, h), # tuple
        'hitbox': {
            'sprite': (offset_x, offset_y, width, height), # tuple
            'strut': (offset_x, offset_y, width, height), # tuple
        # ...
    },
})
```

### State

* tilesets

```python
self.tilesets = munch.Munch({
    'layer_1': {
        'tile_1': {
            'sets': [
                { 
                    'start': {
                        'units': units, # bool
                        'x': x, # int
                        'y': y, # int
                    },
                    'cover': cover, # bool
                }
            ]
        },
    }
})
```

* strutsets

```python
self.strutsets = munch.Munch({
    'layer_1': {
        'strut_1': {
            'sets': [
                { 
                    'start': {
                        'units': units, # bool
                        'x': x, # int
                        'y': y, # int
                    },
                    'cover': cover, # bool
                    'hitbox': (hx, hy, hw, hh), # tuple(int, int, int, int)

                }
            ]
        },
    },
})
```

* platesets

```python
self.platesets = munch.Munch({
    'layer_1': {
        'strut_1': {
            'sets': [
                { 
                    'start': {
                        'units': units, # bool
                        'x': x, # int
                        'y': y, # int
                    },
                    'hitbox': (hx, hy, hw, hh), # tuple(int, int, int, int)
                    'cover': cover, # bool
                    'content': content, # str
                }
            ]
        },
    },
})
```

* compositions

```python
self.compositions = munch.Munch({
    'compose_1': {
        'tiles': {
            'tile_1': {
                'sets': [
                    {
                        'start': {
                            'x': x, # int
                            'y': y, # int
                        },
                        'cover': cover
                    }
                ]
            },
            # ...
        }
        'struts': {
            'strut_1':{
                'sets': [
                    {
                        'start': {
                            'x': x, #int
                            'y': y, #int
                        },
                        'cover': cover, # bool
                    }
                ]
            },
            # ...
        },
        'plates': {
            # ...
        },
    }
})
```

* hero

```python
self.hero = munch.Munch({
    'position': {
        'x': x, # float,
        'y': y, # float
    },
    'stature': {
        'intention': intention, # str
        'action': action, # str
    }
    'state': state, # str,
    'frame': frame, # int
})
```

* npcs

```python
self.npcs = munch.Munch({
    'npc_1': {
        'position: {
            'x': x, # float
            'y': y, # float
        },
        'state': state, # string
        'frame': frame, # int
    },
})
```

### Other

 ```python
self.dimensions = ( w, h ) # tuple
```

```python
self.tile_dimensions = ( w, h ) # tuple
```

```python
self.sprite_dimensions = (  w, h )
```

```python
self.world_bounds = (
    left_bound, # tuple (x,y,w,h)
    top_bound, # tuple (x,y,w,h)
    right_bound, # tuple (x,y,w,h)
    down_bound # tuple(x,y,w,h)
)
```

```python
self.layer = 'one' # str
```

```python
self.layers = [
    'one',
    'two',
    # ...
]
```

```python
self.switch_map = munch.Munch({
    'layer_1': {
        'switch_key_1': {
            'switch_set_index_1': bool_1, # bool
            'switch_set_index_2': bool_2, # bool
            # ...
        },
        # ...
    },
    # ...
})
```