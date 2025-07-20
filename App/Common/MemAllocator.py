class MemAllocator:
    def __init__(self, start=0x0F):
        self.offset = start
        self.entries = []

    def reserve_mem(self, obj, size, align=0x0F, already_aligned=False):
        if not already_aligned:
            self.offset = self._align_mem(self.offset, align)

        obj.offset = self.offset
        self.entries.append((self.offset, obj))
        self.offset += size

        return obj.offset

    def _align_mem(self, memory, alignment):
        return (memory + alignment) & ~alignment