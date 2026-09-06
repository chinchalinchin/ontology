# cython: language_level=3
cdef class Space:
    cdef int cell_size
    cdef int max_entities
    cdef int num_buckets
    cdef int max_per_bucket
    cdef int* bucket_counts
    cdef int* bucket_data

    cpdef void clear(self)
    cdef inline int _hash(self, int cx, int cy)
    cpdef void insert(self, int entity_id, int x, int y, int w, int l)
    cpdef list query(self)