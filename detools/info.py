import os
from .errors import Error
from .apply import unpack_size
from .apply import peek_header_type
from .apply import read_header_normal
from .apply import read_header_in_place
from .apply import PatchReader
from .common import PATCH_TYPE_NORMAL
from .common import PATCH_TYPE_IN_PLACE


def get_patch_size(fpatch):
    fpatch.seek(0, os.SEEK_END)
    patch_size = fpatch.tell()
    fpatch.seek(0, os.SEEK_SET)

    return patch_size


def patch_info_normal_inner(patch_reader, to_size):
    to_pos = 0
    number_of_size_bytes = 0
    diff_sizes = []
    extra_sizes = []
    adjustment_sizes = []

    while to_pos < to_size:
        # Diff data.
        size, number_of_bytes = unpack_size(patch_reader)

        if to_pos + size > to_size:
            raise Error("Patch diff data too long.")

        diff_sizes.append(size)
        number_of_size_bytes += number_of_bytes
        patch_reader.decompress(size)
        to_pos += size

        # Extra data.
        size, number_of_bytes = unpack_size(patch_reader)
        number_of_size_bytes += number_of_bytes

        if to_pos + size > to_size:
            raise Error("Patch extra data too long.")

        extra_sizes.append(size)
        patch_reader.decompress(size)
        to_pos += size

        # Adjustment.
        size, number_of_bytes = unpack_size(patch_reader)
        number_of_size_bytes += number_of_bytes
        adjustment_sizes.append(size)

    return (to_size,
            diff_sizes,
            extra_sizes,
            adjustment_sizes,
            number_of_size_bytes)


def patch_info_normal(fpatch):
    patch_size = get_patch_size(fpatch)
    compression, to_size = read_header_normal(fpatch)

    if to_size == 0:
        info = (0, [], [], [], 0)
    else:
        patch_reader = PatchReader(fpatch, compression)
        info = patch_info_normal_inner(patch_reader, to_size)

        if not patch_reader.eof:
            raise Error('End of patch not found.')

    return (patch_size, compression, *info)


def patch_info_in_place(fpatch):
    patch_size = get_patch_size(fpatch)
    compression, to_size, shift_size = read_header_in_place(fpatch)
    segments = []

    if to_size > 0:
        patch_reader = PatchReader(fpatch, compression)

        while not patch_reader.eof:
            from_offset = unpack_size(patch_reader)[0]
            segment_to_size = read_header_normal(patch_reader)[1]
            info = patch_info_normal_inner(patch_reader, segment_to_size)
            segments.append((from_offset, info))

    return patch_size, compression, to_size, shift_size, segments


def patch_info(fpatch):
    patch_type = peek_header_type(fpatch)

    if patch_type == PATCH_TYPE_NORMAL:
        return 'normal', patch_info_normal(fpatch)
    elif patch_type == PATCH_TYPE_IN_PLACE:
        return 'in-place', patch_info_in_place(fpatch)
    else:
        raise Error('Bad patch type.')
