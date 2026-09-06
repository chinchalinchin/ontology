# cython: language_level=3
from libs.core.models cimport Position, Dimensions, Hitbox, Velocity
from libs.core.math.space cimport Space

cpdef list collisions(list primitive_data, Space grid)

cpdef void collide(
    Position pos1, 
    Hitbox hb1, 
    Velocity vel1, 
    float m1, 
    bint is_kinematic1,
    Position pos2, 
    Hitbox hb2, 
    Velocity vel2, 
    float m2, 
    bint is_kinematic2
)

cpdef void integrate(list assets, float delta)

cpdef void friction(
    Velocity vel, 
    float friction, 
    float delta
)

cpdef void kinematics(
    Velocity vel, 
    float ix, 
    float iy, 
    float speed
)

cpdef void dynamics(
    Velocity vel, 
    float sx, 
    float sy, 
    float tx, 
    float ty, 
    float speed, 
    float impulse, 
    float delta
)