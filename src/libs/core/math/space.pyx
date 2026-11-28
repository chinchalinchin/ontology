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

from libc.stdlib cimport malloc, calloc, free
from libc.string cimport memset, memcpy


cdef inline int _hash_cell(int cx, int cy, int num_buckets) noexcept nogil:
    cdef unsigned int h = (<unsigned int>cx * 73856093u) ^ (<unsigned int>cy * 19349663u)
    return <int>(h % <unsigned int>num_buckets)


cdef inline void _reset_pair_table(Space grid) noexcept:
    grid.pair_epoch += 1
    if grid.pair_epoch == 0:
        memset(grid.pair_stamps, 0, <size_t>grid.pair_cap * sizeof(unsigned int))
        grid.pair_epoch = 1
    grid.pair_count = 0


cdef void _grow_pair_table(Space grid) except *:
    cdef int old_cap = grid.pair_cap
    cdef int new_cap = old_cap * 2
    cdef unsigned long long* new_keys = <unsigned long long*>malloc(
        <size_t>new_cap * sizeof(unsigned long long)
    )
    cdef unsigned int* new_stamps = <unsigned int*>calloc(
        <size_t>new_cap, sizeof(unsigned int)
    )
    if new_keys is NULL or new_stamps is NULL:
        if new_keys is not NULL:
            free(new_keys)
        if new_stamps is not NULL:
            free(new_stamps)
        raise MemoryError()

    cdef unsigned long long mask = <unsigned long long>(new_cap - 1)
    cdef unsigned int epoch = grid.pair_epoch
    cdef unsigned long long key
    cdef int i, slot

    for i in range(old_cap):
        if grid.pair_stamps[i] == epoch:
            key = grid.pair_keys[i]
            slot = <int>(((key ^ (key >> 33)) * 11400714819323198485ULL) & mask)
            while new_stamps[slot] == epoch:
                slot = (slot + 1) & <int>mask
            new_stamps[slot] = epoch
            new_keys[slot] = key

    free(grid.pair_keys)
    free(grid.pair_stamps)
    grid.pair_keys = new_keys
    grid.pair_stamps = new_stamps
    grid.pair_cap = new_cap


cdef void _grow_pair_out(Space grid) except *:
    cdef int new_cap = grid.pair_out_cap * 2
    cdef int* new_a = <int*>malloc(<size_t>new_cap * sizeof(int))
    cdef int* new_b = <int*>malloc(<size_t>new_cap * sizeof(int))
    if new_a is NULL or new_b is NULL:
        if new_a is not NULL:
            free(new_a)
        if new_b is not NULL:
            free(new_b)
        raise MemoryError()

    if grid.pair_count > 0:
        memcpy(new_a, grid.pair_a, <size_t>grid.pair_count * sizeof(int))
        memcpy(new_b, grid.pair_b, <size_t>grid.pair_count * sizeof(int))

    free(grid.pair_a)
    free(grid.pair_b)
    grid.pair_a = new_a
    grid.pair_b = new_b
    grid.pair_out_cap = new_cap


cdef inline bint _record_pair(Space grid, int id1, int id2) except -1:
    if (grid.pair_count + 1) * 2 >= grid.pair_cap:
        _grow_pair_table(grid)

    cdef unsigned long long key = (
        (<unsigned long long>(<unsigned int>id1) << 32)
        | <unsigned long long>(<unsigned int>id2)
    )
    cdef int mask = grid.pair_cap - 1
    cdef unsigned int epoch = grid.pair_epoch
    cdef int slot = <int>(
        ((key ^ (key >> 33)) * 11400714819323198485ULL)
        & <unsigned long long>mask
    )

    while grid.pair_stamps[slot] == epoch:
        if grid.pair_keys[slot] == key:
            return False
        slot = (slot + 1) & mask

    grid.pair_stamps[slot] = epoch
    grid.pair_keys[slot] = key

    if grid.pair_count >= grid.pair_out_cap:
        _grow_pair_out(grid)

    grid.pair_a[grid.pair_count] = id1
    grid.pair_b[grid.pair_count] = id2
    grid.pair_count += 1
    return True


cdef class Space:
    """
    Uniform grid spatial hash storing integer entity IDs in flat C buckets
    with active-bucket tracking, dynamic per-bucket capacity expansion, and
    zero-allocation C-level pair deduplication.
    """

    def __init__(self, int cell_size=64, int max_entities=2000):
        """Allocates flat C-backed spatial hash bucket and pair buffers."""
        if cell_size <= 0:
            cell_size = 64
        if max_entities <= 0:
            max_entities = 1

        self.cell_size = cell_size
        self.max_entities = max_entities
        self.num_buckets = max_entities * 2
        self.max_per_bucket = 50
        self.active_count = 0
        self.pair_cap = 256
        self.pair_out_cap = 256
        self.pair_count = 0
        self.pair_epoch = 0

        self.bucket_counts = <int*>calloc(<size_t>self.num_buckets, sizeof(int))
        self.bucket_data = <int*>malloc(
            <size_t>self.num_buckets * <size_t>self.max_per_bucket * sizeof(int)
        )
        self.active_buckets = <int*>malloc(<size_t>self.num_buckets * sizeof(int))
        self.pair_keys = <unsigned long long*>malloc(
            <size_t>self.pair_cap * sizeof(unsigned long long)
        )
        self.pair_stamps = <unsigned int*>calloc(
            <size_t>self.pair_cap, sizeof(unsigned int)
        )
        self.pair_a = <int*>malloc(<size_t>self.pair_out_cap * sizeof(int))
        self.pair_b = <int*>malloc(<size_t>self.pair_out_cap * sizeof(int))

        if (
            self.bucket_counts is NULL
            or self.bucket_data is NULL
            or self.active_buckets is NULL
            or self.pair_keys is NULL
            or self.pair_stamps is NULL
            or self.pair_a is NULL
            or self.pair_b is NULL
        ):
            raise MemoryError()

    def __dealloc__(self):
        if self.bucket_counts is not NULL:
            free(self.bucket_counts)
            self.bucket_counts = NULL
        if self.bucket_data is not NULL:
            free(self.bucket_data)
            self.bucket_data = NULL
        if self.active_buckets is not NULL:
            free(self.active_buckets)
            self.active_buckets = NULL
        if self.pair_keys is not NULL:
            free(self.pair_keys)
            self.pair_keys = NULL
        if self.pair_stamps is not NULL:
            free(self.pair_stamps)
            self.pair_stamps = NULL
        if self.pair_a is not NULL:
            free(self.pair_a)
            self.pair_a = NULL
        if self.pair_b is not NULL:
            free(self.pair_b)
            self.pair_b = NULL

    cpdef void clear(self):
        """Resets only occupied buckets in O(active_count) time."""
        cdef int i
        if self.bucket_counts is not NULL and self.active_buckets is not NULL:
            for i in range(self.active_count):
                self.bucket_counts[self.active_buckets[i]] = 0
        self.active_count = 0

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
        cdef int old_cap, new_cap, b_idx, b, cnt
        cdef int* new_data

        for cx in range(min_x, max_x + 1):
            for cy in range(min_y, max_y + 1):
                h = _hash_cell(cx, cy, self.num_buckets)
                count = self.bucket_counts[h]
                if count == 0:
                    self.active_buckets[self.active_count] = h
                    self.active_count += 1
                elif self.bucket_data[h * self.max_per_bucket + count - 1] == entity_id:
                    continue
                elif count >= self.max_per_bucket:
                    # Double per-bucket stride to prevent silent entity dropping
                    old_cap = self.max_per_bucket
                    new_cap = old_cap * 2
                    new_data = <int*>malloc(
                        <size_t>self.num_buckets * <size_t>new_cap * sizeof(int)
                    )
                    if new_data is NULL:
                        raise MemoryError()
                    for b_idx in range(self.active_count):
                        b = self.active_buckets[b_idx]
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

    cdef int query_pairs(self) except -1:
        """
        Populates self.pair_a / self.pair_b with all unique unordered candidate
        pairs across active buckets and returns the pair count without Python allocations.
        """
        cdef int a_idx, b, base, i, j, count, id1, id2

        _reset_pair_table(self)
        for a_idx in range(self.active_count):
            b = self.active_buckets[a_idx]
            count = self.bucket_counts[b]
            if count > 1:
                base = b * self.max_per_bucket
                for i in range(count):
                    for j in range(i + 1, count):
                        id1 = self.bucket_data[base + i]
                        id2 = self.bucket_data[base + j]
                        if id1 == id2:
                            continue
                        if id1 > id2:
                            id1, id2 = id2, id1
                        _record_pair(self, id1, id2)

        return self.pair_count

    cdef int query_bipartite_pairs(self) except -1:
        """
        Populates self.pair_a (< 0) and self.pair_b (>= 0) with unique bipartite
        candidate pairs across active buckets, skipping negative-vs-negative and
        positive-vs-positive pairs entirely.
        """
        cdef int a_idx, b, base, i, j, count, id_pos, id_neg

        _reset_pair_table(self)
        for a_idx in range(self.active_count):
            b = self.active_buckets[a_idx]
            count = self.bucket_counts[b]
            if count > 1:
                base = b * self.max_per_bucket
                for i in range(count):
                    id_pos = self.bucket_data[base + i]
                    if id_pos < 0:
                        continue
                    for j in range(count):
                        id_neg = self.bucket_data[base + j]
                        if id_neg < 0:
                            _record_pair(self, id_neg, id_pos)

        return self.pair_count

    cdef int probe_aabb(self, int x, int y, int w, int l) except -1:
        """
        Probes buckets overlapped by half-open AABB [x, x + w) x [y, y + l)
        against a pre-populated Space without mutating buckets. Writes unique
        stored IDs into self.pair_b[0..n-1] and returns n.
        """
        if w <= 0 or l <= 0 or self.active_count == 0:
            return 0

        _reset_pair_table(self)

        cdef int min_x = x // self.cell_size
        cdef int min_y = y // self.cell_size
        cdef int max_x = (x + w - 1) // self.cell_size
        cdef int max_y = (y + l - 1) // self.cell_size
        cdef int cx, cy, h, count, i, base

        for cx in range(min_x, max_x + 1):
            for cy in range(min_y, max_y + 1):
                h = _hash_cell(cx, cy, self.num_buckets)
                count = self.bucket_counts[h]
                if count > 0:
                    base = h * self.max_per_bucket
                    for i in range(count):
                        _record_pair(self, 0, self.bucket_data[base + i])

        return self.pair_count

    # Promoted to cpdef for Python test accessibility
    cpdef list query(self):
        """Returns unique unordered candidate (id1, id2) pairs across occupied buckets."""
        cdef int n = self.query_pairs()
        cdef list pairs = []
        cdef int k
        for k in range(n):
            pairs.append((self.pair_a[k], self.pair_b[k]))
        return pairs