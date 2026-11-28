# cython: language_level=3
"""
@domain.logic
@domain.system
@app.library
@physics.space
@workflow.combat
@workflow.collisions

# Ontology: Libraries - libs.core.math.space

Cython header for spatial hash grid broad-phase collision queries.
"""

cdef class Space:
    cdef public int cell_size
    cdef public int max_entities
    cdef int num_buckets
    cdef int max_per_bucket
    cdef int* bucket_counts
    cdef int* bucket_data
    cdef int* active_buckets
    cdef int active_count
    cdef unsigned long long* pair_keys
    cdef unsigned int* pair_stamps
    cdef unsigned int pair_epoch
    cdef int pair_cap
    cdef int pair_count
    cdef int* pair_a
    cdef int* pair_b
    cdef int pair_out_cap

    cdef int query_pairs(self) except -1
    cdef int query_bipartite_pairs(self) except -1
    cdef int probe_aabb(self, int x, int y, int w, int l) except -1
    cpdef void clear(self)
    cpdef void insert(self, int entity_id, int x, int y, int w, int l)
    cpdef list query(self)