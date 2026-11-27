"""
@domain.system
@domain.model
@app.library
@workflow.collisions

# Ontology: Libraries - libs.core.models
"""
# cython: language_level=3


cdef class Position:
    """
    Discrete world-space coordinate (x, y) with sub-pixel integration remainders (rx, ry).
    """

    def __init__(self, int x, int y, double rx=0.0, double ry=0.0):
        self.x = x
        self.y = y
        self.rx = rx
        self.ry = ry

    def __eq__(self, object other):
        cdef Position o
        if not isinstance(other, Position):
            return NotImplemented
        o = <Position>other
        return self.x == o.x and self.y == o.y

    def __ne__(self, object other):
        cdef Position o
        if not isinstance(other, Position):
            return NotImplemented
        o = <Position>other
        return self.x != o.x or self.y != o.y

    def __repr__(self) -> str:
        return f"Position(x={self.x}, y={self.y})"

    def __reduce__(self):
        return (Position, (self.x, self.y, self.rx, self.ry))

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y, "rx": self.rx, "ry": self.ry}


cdef class Dimensions:
    """
    Width (w) and length (l) extents in pixels.
    """

    def __init__(self, int w, int l):
        self.w = w
        self.l = l

    def __eq__(self, object other):
        cdef Dimensions o
        if not isinstance(other, Dimensions):
            return NotImplemented
        o = <Dimensions>other
        return self.w == o.w and self.l == o.l

    def __ne__(self, object other):
        cdef Dimensions o
        if not isinstance(other, Dimensions):
            return NotImplemented
        o = <Dimensions>other
        return self.w != o.w or self.l != o.l

    def __repr__(self) -> str:
        return f"Dimensions(w={self.w}, l={self.l})"

    def __reduce__(self):
        return (Dimensions, (self.w, self.l))

    def to_dict(self) -> dict:
        return {"w": self.w, "l": self.l}


cdef class Multiple:
    """
    Discrete horizontal (nx) and vertical (ny) tile/craft repetition factors.
    """

    def __init__(self, int nx, int ny):
        self.nx = nx
        self.ny = ny

    def __eq__(self, object other):
        cdef Multiple o
        if not isinstance(other, Multiple):
            return NotImplemented
        o = <Multiple>other
        return self.nx == o.nx and self.ny == o.ny

    def __ne__(self, object other):
        cdef Multiple o
        if not isinstance(other, Multiple):
            return NotImplemented
        o = <Multiple>other
        return self.nx != o.nx or self.ny != o.ny

    def __repr__(self) -> str:
        return f"Multiple(nx={self.nx}, ny={self.ny})"

    def __reduce__(self):
        return (Multiple, (self.nx, self.ny))

    def to_dict(self) -> dict:
        return {"nx": self.nx, "ny": self.ny}


cdef class Velocity:
    """
    Two-dimensional velocity vector (vx, vy) in pixels per second.
    """

    def __init__(self, double vx, double vy):
        self.vx = vx
        self.vy = vy

    def __eq__(self, object other):
        cdef Velocity o
        if not isinstance(other, Velocity):
            return NotImplemented
        o = <Velocity>other
        return self.vx == o.vx and self.vy == o.vy

    def __ne__(self, object other):
        cdef Velocity o
        if not isinstance(other, Velocity):
            return NotImplemented
        o = <Velocity>other
        return self.vx != o.vx or self.vy != o.vy

    def __repr__(self) -> str:
        return f"Velocity(vx={self.vx}, vy={self.vy})"

    def __reduce__(self):
        return (Velocity, (self.vx, self.vy))

    def to_dict(self) -> dict:
        return {"vx": self.vx, "vy": self.vy}


cdef class Hitbox:
    """
    Relative AABB collision primitive combining Position and Dimensions.
    """

    def __init__(self, Position position, Dimensions dimensions):
        self.position = position
        self.dimensions = dimensions

    def __eq__(self, object other):
        cdef Hitbox o
        if not isinstance(other, Hitbox):
            return NotImplemented
        o = <Hitbox>other
        return self.position == o.position and self.dimensions == o.dimensions

    def __ne__(self, object other):
        cdef Hitbox o
        if not isinstance(other, Hitbox):
            return NotImplemented
        o = <Hitbox>other
        return self.position != o.position or self.dimensions != o.dimensions

    def __repr__(self) -> str:
        return f"Hitbox(position={self.position!r}, dimensions={self.dimensions!r})"

    def __reduce__(self):
        return (Hitbox, (self.position, self.dimensions))

    def to_dict(self) -> dict:
        return {
            "position": self.position.to_dict() if self.position is not None else None,
            "dimensions": self.dimensions.to_dict() if self.dimensions is not None else None
        }


cdef class Scale:
    """
    Screen position represented as percentages.
    """
    cdef public double pw
    cdef public double pl

    def __init__(self, double pw, double pl):
        self.pw = pw
        self.pl = pl

    def __eq__(self, object other):
        cdef Scale o
        if not isinstance(other, Scale):
            return NotImplemented
        o = <Scale>other
        return self.pw == o.pw and self.pl == o.pl

    def __ne__(self, object other):
        cdef Scale o
        if not isinstance(other, Scale):
            return NotImplemented
        o = <Scale>other
        return self.pw != o.pw or self.pl != o.pl

    def __repr__(self) -> str:
        return f"Scale(pw={self.pw}, pl={self.pl})"

    def __reduce__(self):
        return (Scale, (self.pw, self.pl))

    def to_dict(self) -> dict:
        return {"pw": self.pw, "pl": self.pl}


cdef class Boundary:
    """
    Absolute world-space environmental constraint.
    """

    def __init__(self, Position position, Dimensions dimensions):
        self.position = position
        self.dimensions = dimensions

    def __eq__(self, object other):
        cdef Boundary o
        if not isinstance(other, Boundary):
            return NotImplemented
        o = <Boundary>other
        return self.position == o.position and self.dimensions == o.dimensions

    def __ne__(self, object other):
        cdef Boundary o
        if not isinstance(other, Boundary):
            return NotImplemented
        o = <Boundary>other
        return self.position != o.position or self.dimensions != o.dimensions

    def __repr__(self) -> str:
        return f"Boundary(position={self.position!r}, dimensions={self.dimensions!r})"

    def __reduce__(self):
        return (Boundary, (self.position, self.dimensions))

    def to_dict(self) -> dict:
        return {
            "position": self.position.to_dict() if self.position is not None else None,
            "dimensions": self.dimensions.to_dict() if self.dimensions is not None else None
        }

    def primitive(self) -> tuple:
        return (
            self.position.x,
            self.position.y,
            self.dimensions.w,
            self.dimensions.l
        )