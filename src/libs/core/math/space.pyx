# cython: language_level=3
from libc.stdlib cimport malloc, free
from libc.string cimport memset

cdef class Space:
    def __init__(self, int cell_size=64, int max_entities=2000):
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

    cdef inline int _hash(self, int cx, int cy):
        return (abs(cx * 73856093 ^ cy * 19349663)) % self.num_buckets

    # Promoted to cpdef for Python test accessibility
    cpdef void insert(self, int entity_id, int x, int y, int w, int l):
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
                        if id1 > id2:
                            id1, id2 = id2, id1
                        pair = (id1, id2)
                        if pair not in seen:
                            seen.add(pair)
                            pairs.append(pair)
        return pairs