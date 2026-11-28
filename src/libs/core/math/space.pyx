"""
@domain.logic
@domain.system
@app.library
@physics.space
@workflow.combat
@workflow.collisions

# Ontology: Libraries - libs.core.math.space

Spatial hash grid for broad-phase collision candidate queries.
"""
# cython: language_level=3

from libc.stdlib cimport malloc, free
from libc.string cimport memset, memcpy

cdef class Space:
    """
    Uniform grid spatial hash storing integer entity IDs in flat C buckets
    with dynamic per-bucket capacity expansion.
    """
    def __init__(self, int cell_size=64, int max_entities=2000):
        """Allocates flat C-backed spatial hash bucket buffers."""
        self.cell_size = cell_size
        self.max_entities = max_entities
        self.num_buckets = max_entities * 2
        self.max_per_bucket = 50
        self.bucket_counts = <int*>malloc(<size_t>self.num_buckets * sizeof(int))
        self.bucket_data = <int*>malloc(
            <size_t>self.num_buckets * <size_t>self.max_per_bucket * sizeof(int)
        )
        if self.bucket_counts is NULL or self.bucket_data is NULL:
            if self.bucket_counts is not NULL:
                free(self.bucket_counts)
                self.bucket_counts = NULL
            if self.bucket_data is not NULL:
                free(self.bucket_data)
                self.bucket_data = NULL
            raise MemoryError()
        self.clear()

    def __dealloc__(self):
        if self.bucket_counts is not NULL:
            free(self.bucket_counts)
        if self.bucket_data is not NULL:
            free(self.bucket_data)

    cpdef void clear(self):
        if self.bucket_counts is not NULL:
            memset(self.bucket_counts, 0, <size_t>self.num_buckets * sizeof(int))

    cdef inline int _hash(self, int cx, int cy) noexcept nogil:
        cdef unsigned int h = (<unsigned int>cx * 73856093u) ^ (<unsigned int>cy * 19349663u)
        return <int>(h % <unsigned int>self.num_buckets)

    # Promoted to cpdef for Python test accessibility
    cpdef void insert(self, int entity_id, int x, int y, int w, int l):
        """
        Inserts an entity into all grid cells overlapped by its half-open AABB
        [x, x + w) x [y, y + l), expanding bucket stride dynamically on overflow.
        """
        if w <= 0 or l <= 0:
            return

        cdef int min_x = x // self.cell_size
        cdef int min_y = y // self.cell_size
        cdef int max_x = (x + w - 1) // self.cell_size
        cdef int max_y = (y + l - 1) // self.cell_size
        cdef int cx, cy, h, count, idx
        cdef int old_cap, new_cap, b, cnt
        cdef int* new_data

        for cx in range(min_x, max_x + 1):
            for cy in range(min_y, max_y + 1):
                h = self._hash(cx, cy)
                count = self.bucket_counts[h]
                if count > 0 and self.bucket_data[h * self.max_per_bucket + count - 1] == entity_id:
                    continue
                if count >= self.max_per_bucket:
                    # Double per-bucket stride to prevent silent entity dropping
                    old_cap = self.max_per_bucket
                    new_cap = old_cap * 2
                    new_data = <int*>malloc(
                        <size_t>self.num_buckets * <size_t>new_cap * sizeof(int)
                    )
                    if new_data is NULL:
                        raise MemoryError()
                    for b in range(self.num_buckets):
                        cnt = self.bucket_counts[b]
                        if cnt > 0:
                            memcpy(
                                &new_data[b * new_cap],
                                &self.bucket_data[b * old_cap],
                                <size_t>cnt * sizeof(int)
                            )
                    free(self.bucket_data)
                    self.bucket_data = new_data
                    self.max_per_bucket = new_cap
                idx = h * self.max_per_bucket + count
                self.bucket_data[idx] = entity_id
                self.bucket_counts[h] = count + 1

    # Promoted to cpdef for Python test accessibility
    cpdef list query(self):
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
                        if id1 == id2:
                            continue
                        if id1 > id2:
                            id1, id2 = id2, id1
                        pair = (id1, id2)
                        if pair not in seen:
                            seen.add(pair)
                            pairs.append(pair)
        return pairs