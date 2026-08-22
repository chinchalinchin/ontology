# cython: language_level=3
"""
# Ontology: libs.core.math

Cythonized high-performance geometry and physics logic.
"""
# Standard Libraries
from typing import List

# Cython Libraries
from libs.core.models cimport Position, Dimensions, Hitbox
from libc.stdlib cimport malloc, free
from libc.string cimport memset

cdef class Geometry:
    """
    Static utility class for geometric calculations.
    """

    @staticmethod
    cdef tuple _intersects(
        Position pos1, 
        Dimensions dim1, 
        list hitboxes1,
        Position pos2, 
        Dimensions dim2, 
        list hitboxes2
    ):
        """
        Calculates AABB intersection between two entities at native C-speeds.
        """
        cdef int x1, y1, w1, h1
        cdef int x2, y2, w2, h2
        cdef Hitbox hb1, hb2
        
        # Fast path: If an object doesn't have hitboxes (e.g., background tiles), 
        # they inherently cannot collide in this engine's narrow phase.
        if not hitboxes1 or not hitboxes2:
            return None
        
        # Iterate over hitboxes. 
        # Notice we typecast `<Hitbox>item` so Cython knows the exact memory layout 
        # and doesn't fall back to standard Python dict lookups inside the loop.
        for item1 in hitboxes1:
            hb1 = <Hitbox>item1
            x1 = pos1.x + hb1.position.x
            y1 = pos1.y + hb1.position.y
            w1 = hb1.dimensions.w
            h1 = hb1.dimensions.l
        
            for item2 in hitboxes2:
                hb2 = <Hitbox>item2
                x2 = pos2.x + hb2.position.x
                y2 = pos2.y + hb2.position.y
                w2 = hb2.dimensions.w
                h2 = hb2.dimensions.l
                
                # Inline AABB collision check using the integer primitives 
                if (x1 < x2 + w2 and x1 + w1 > x2 and
                    y1 < y2 + h2 and y1 + h1 > y2):
                    return (hb1, hb2)
                    
        return None

    @staticmethod
    def intersects(
        Position pos1, 
        Dimensions dim1, 
        list hitboxes1,
        Position pos2, 
        Dimensions dim2, 
        list hitboxes2
    ):
        """
        Python-accessible wrapper for the Cython _intersects method.
        """
        return Geometry._intersects(pos1, dim1, hitboxes1, pos2, dim2, hitboxes2)

    @staticmethod
    cdef bint onscreen(
        Position pos, 
        Dimensions dim, 
        Position p_pos, 
        Dimensions p_dim, 
        Dimensions screen
    ):
        """
        Fast AABB camera culling check. Evaluates if the asset intersects with 
        the camera's viewport (centered on the player).
        """
        # Calculate camera top-left (without board-clamping for raw speed)
        cdef int cam_x = p_pos.x + (p_dim.l // 2) - (screen.w // 2)
        cdef int cam_y = p_pos.y + (p_dim.w // 2) - (screen.l // 2)
        
        return (pos.x < cam_x + screen.w and pos.x + dim.w > cam_x and
                pos.y < cam_y + screen.l and pos.y + dim.l > cam_y)

cdef class Space:
    """
    Broad-Phase Spatial Partitioning Grid for O(1) bucket lookups.
    """
    def __init__(self, 
        int cell_size=64, 
        int max_entities=2000
    ):
        self.cell_size = cell_size
        self.max_entities = max_entities
        self.num_buckets = max_entities * 2
        self.max_per_bucket = 50
        self.bucket_counts = <int*>malloc(self.num_buckets * sizeof(int))
        self.bucket_data = <int*>malloc(self.num_buckets * self.max_per_bucket * sizeof(int))
        self.clear()

    def __dealloc__(self):
        if self.bucket_counts is not NULL:
            free(self.bucket_counts)
        if self.bucket_data is not NULL:
            free(self.bucket_data)

    cpdef void clear(self):
        if self.bucket_counts is not NULL:
            memset(self.bucket_counts, 0, self.num_buckets * sizeof(int))

    cdef inline int _hash(self,
        int cx, 
        int cy
    ):
        return (abs(cx * 73856093 ^ cy * 19349663)) % self.num_buckets

    cdef void insert(self, 
        int entity_id, 
        int x, 
        int y, 
        int w, 
        int l
    ):
        cdef int min_x = x // self.cell_size
        cdef int min_y = y // self.cell_size
        cdef int max_x = (x + w) // self.cell_size
        cdef int max_y = (y + l) // self.cell_size
        cdef int cx, cy, h, idx

        for cx in range(min_x, max_x + 1):
            for cy in range(min_y, max_y + 1):
                h = self._hash(cx, cy)
                if self.bucket_counts[h] < self.max_per_bucket:
                    idx = h * self.max_per_bucket + self.bucket_counts[h]
                    self.bucket_data[idx] = entity_id
                    self.bucket_counts[h] += 1

    cdef list query(self):
        cdef list pairs = []
        cdef set seen = set()
        cdef int b, i, j, count, id1, id2
        cdef tuple pair

        for b in range(self.num_buckets):
            count = self.bucket_counts[b]
            if count > 1:
                for i in range(count):
                    for j in range(i + 1, count):
                        id1 = self.bucket_data[b * self.max_per_bucket + i]
                        id2 = self.bucket_data[b * self.max_per_bucket + j]
                        if id1 > id2:
                            id1, id2 = id2, id1
                        pair = (id1, id2)
                        if pair not in seen:
                            seen.add(pair)
                            pairs.append(pair)
        return pairs

cdef class Physics:
    """
    Static utility class for broad-phase and narrow-phase physics resolution.
    """

    @staticmethod
    def collisions(
        list primitive_data, 
        Space grid
    ) -> list:
        """
        Iterates over a list of primitive spatial data tuples and resolves geometric overlap.
        Returns a Python list of colliding integer ID pairs.
        """
        cdef int i, x, y, w, l
        cdef tuple data
        
        # 1. Broad-Phase Spatial Hash (Populate)
        for data in primitive_data:
            i = data[0]
            x = data[1]
            y = data[2]
            w = data[3]
            l = data[4]
            grid.insert(i, x, y, w, l)
            
        # 2. Broad-Phase Query Pairs
        cdef list candidate_pairs = grid.query()
        
        # 3. Narrow-Phase Detection
        cdef list colliding_pairs = []
        cdef int id_a, id_b
        cdef tuple data_a, data_b
        
        # Pre-allocate to adhere to the "Zero Heap Allocation" inner loop philosophy
        cdef Position pos_a = Position(0, 0)
        cdef Dimensions dim_a = Dimensions(0, 0)
        cdef Position pos_b = Position(0, 0)
        cdef Dimensions dim_b = Dimensions(0, 0)
        cdef tuple pair
        
        for pair in candidate_pairs:
            id_a = pair[0]
            id_b = pair[1]
            data_a = primitive_data[id_a]
            data_b = primitive_data[id_b]
            
            pos_a.x = data_a[1]
            pos_a.y = data_a[2]
            dim_a.w = data_a[3]
            dim_a.l = data_a[4]

            pos_b.x = data_b[1]
            pos_b.y = data_b[2]
            dim_b.w = data_b[3]
            dim_b.l = data_b[4]

            if Geometry._intersects(pos_a, dim_a, data_a[5], pos_b, dim_b, data_b[5]) is not None:
                colliding_pairs.append(pair)
                
        return colliding_pairs

    @staticmethod
    def resolve_collision(
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
    ):
        cdef float cx_a = pos1.x + hb1.position.x + hb1.dimensions.w / 2.0
        cdef float cy_a = pos1.y + hb1.position.y + hb1.dimensions.l / 2.0
        cdef float cx_b = pos2.x + hb2.position.x + hb2.dimensions.w / 2.0
        cdef float cy_b = pos2.y + hb2.position.y + hb2.dimensions.l / 2.0

        cdef float dx = cx_b - cx_a
        cdef float dy = cy_b - cy_a

        if dx == 0 and dy == 0:
            dx = 1.0

        cdef float overlap_x = (hb1.dimensions.w / 2.0 + hb2.dimensions.w / 2.0) - abs(dx)
        cdef float overlap_y = (hb1.dimensions.l / 2.0 + hb2.dimensions.l / 2.0) - abs(dy)

        cdef float inv_m1, inv_m2, inv_total, p1, p2
        cdef float shift_x1, shift_x2, shift_y1, shift_y2
        cdef float v1x, v1y, v2x, v2y, v1f_x, v1f_y, v2f_x, v2f_y

        if overlap_x > 0 and overlap_y > 0:
            inv_m1 = 1.0 / m1 if m1 > 0 else 0.0
            inv_m2 = 1.0 / m2 if m2 > 0 else 0.0
            inv_total = inv_m1 + inv_m2

            if inv_total > 0:
                p1 = inv_m1 / inv_total
                p2 = inv_m2 / inv_total

                if overlap_x < overlap_y:
                    shift_x1 = overlap_x * p1
                    shift_x2 = overlap_x * p2
                    if dx > 0:
                        pos1.x -= int(shift_x1)
                        pos2.x += int(shift_x2)
                    else:
                        pos1.x += int(shift_x1)
                        pos2.x -= int(shift_x2)

                    if m1 == 0 and m2 == 0:
                        pass
                    elif m1 == 0:
                        if vel2 is not None and not is_kinematic2:
                            vel2.vx = -vel2.vx
                    elif m2 == 0:
                        if vel1 is not None and not is_kinematic1:
                            vel1.vx = -vel1.vx
                    else:
                        v1x = vel1.vx if vel1 is not None else 0.0
                        v2x = vel2.vx if vel2 is not None else 0.0
                        v1f_x = (v1x * (m1 - m2) + 2 * m2 * v2x) / (m1 + m2)
                        v2f_x = (v2x * (m2 - m1) + 2 * m1 * v1x) / (m1 + m2)
                        
                        if vel1 is not None and not is_kinematic1:
                            vel1.vx = v1f_x
                        if vel2 is not None and not is_kinematic2:
                            vel2.vx = v2f_x
                else:
                    shift_y1 = overlap_y * p1
                    shift_y2 = overlap_y * p2
                    if dy > 0:
                        pos1.y -= int(shift_y1)
                        pos2.y += int(shift_y2)
                    else:
                        pos1.y += int(shift_y1)
                        pos2.y -= int(shift_y2)

                    if m1 == 0 and m2 == 0:
                        pass
                    elif m1 == 0:
                        if vel2 is not None and not is_kinematic2:
                            vel2.vy = -vel2.vy
                    elif m2 == 0:
                        if vel1 is not None and not is_kinematic1:
                            vel1.vy = -vel1.vy
                    else:
                        v1y = vel1.vy if vel1 is not None else 0.0
                        v2y = vel2.vy if vel2 is not None else 0.0
                        v1f_y = (v1y * (m1 - m2) + 2 * m2 * v2y) / (m1 + m2)
                        v2f_y = (v2y * (m2 - m1) + 2 * m1 * v1y) / (m1 + m2)
                        
                        if vel1 is not None and not is_kinematic1:
                            vel1.vy = v1f_y
                        if vel2 is not None and not is_kinematic2:
                            vel2.vy = v2f_y

    @staticmethod
    def integrate_kinematics(
        list assets, 
        float delta
    ):
        cdef int shift
        cdef Position p
        cdef Velocity v
        for asset in assets:
            if getattr(asset.state, 'velocity', None) is not None:
                p = <Position>asset.state.position
                v = <Velocity>asset.state.velocity

                p.rx += v.vx * delta
                p.ry += v.vy * delta

                if p.rx >= 1.0 or p.rx <= -1.0:
                    shift = int(p.rx)
                    p.x += shift
                    p.rx -= shift

                if p.ry >= 1.0 or p.ry <= -1.0:
                    shift = int(p.ry)
                    p.y += shift
                    p.ry -= shift