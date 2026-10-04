"""Orthographic software z-buffer for truthful occlusion, no image libraries.

Presentation only. Colours are component identifiers, NEVER temperatures.
"""
import math
import struct
import zlib

from geometry import cross, dot, subtract, unit


def project(point, yaw=.55, pitch=.40):
    x, y, z = point
    horizontal = math.cos(yaw) * x + math.sin(yaw) * y
    depth = -math.sin(yaw) * x + math.cos(yaw) * y
    return (horizontal, -math.cos(pitch) * z - math.sin(pitch) * depth,
            math.cos(pitch) * depth - math.sin(pitch) * z)


def shade(colour, points):
    normal = cross(subtract(points[1], points[0]), subtract(points[2], points[0]))
    strength = .8 if dot(normal, normal) < 1e-12 else .62 + .38 * abs(dot(unit(normal), unit((.3, -.5, 1))))
    return tuple(int(int(colour[i:i + 2], 16) * strength) for i in (1, 3, 5))


def rasterize_projected(faces, width, height, draw_edges=True, edge_depth_bias=3):
    """Projected polygon coordinates are screen x/y and linear eye depth.

    Smaller depth is closer. Opaque triangles are order-independent. Only
    actual polygon edges are outlined, not artificial fan triangulation.
    """
    rgba = bytearray(width * height * 4)
    depths = [math.inf] * (width * height)
    for face in faces:
        points, colour = face["points"], face["rgb"]
        for i in range(1, len(points) - 1):
            a, b, c = points[0], points[i], points[i + 1]
            denom = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(denom) < 1e-10:
                continue
            xmin = max(0, math.floor(min(a[0], b[0], c[0])))
            xmax = min(width - 1, math.ceil(max(a[0], b[0], c[0])))
            ymin = max(0, math.floor(min(a[1], b[1], c[1])))
            ymax = min(height - 1, math.ceil(max(a[1], b[1], c[1])))
            for y in range(ymin, ymax + 1):
                yy = y + .5 - c[1]
                for x in range(xmin, xmax + 1):
                    xx = x + .5 - c[0]
                    wa = ((b[1] - c[1]) * xx + (c[0] - b[0]) * yy) / denom
                    wb = ((c[1] - a[1]) * xx + (a[0] - c[0]) * yy) / denom
                    wc = 1 - wa - wb
                    if min(wa, wb, wc) < -1e-8:
                        continue
                    depth = wa * a[2] + wb * b[2] + wc * c[2]
                    index = y * width + x
                    if depth < depths[index]:
                        depths[index] = depth
                        offset = index * 4
                        rgba[offset:offset + 4] = bytes((*colour, 255))
    if draw_edges:
        for face in faces:
            points = face["points"]
            for a, b in zip(points, points[1:] + points[:1]):
                steps = max(1, math.ceil(max(abs(b[0] - a[0]), abs(b[1] - a[1]))))
                for step in range(steps + 1):
                    t = step / steps
                    x, y = round(a[0] + t * (b[0] - a[0])), round(a[1] + t * (b[1] - a[1]))
                    if not (0 <= x < width and 0 <= y < height):
                        continue
                    index = y * width + x
                    depth = a[2] + t * (b[2] - a[2])
                    if depth <= depths[index] + edge_depth_bias:
                        offset = index * 4
                        rgba[offset:offset + 4] = bytes((70, 89, 100, 255))
    return rgba


def png_bytes(rgba, width, height):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    raw = b"".join(b"\0" + rgba[y * width * 4:(y + 1) * width * 4] for y in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def render(case, width=1030, height=795):
    visible = [f for f in case["mesh"] if f["group"] not in ("mechanisms", "collector", "underfloor")]
    mapped = [[project(p) for p in f["points"]] for f in visible]
    points = [p for face in mapped for p in face]
    xmin, xmax = min(p[0] for p in points), max(p[0] for p in points)
    ymin, ymax = min(p[1] for p in points), max(p[1] for p in points)
    scale = min((width - 30) / (xmax - xmin), (height - 30) / (ymax - ymin))
    ox, oy = width / 2 - (xmin + xmax) / 2 * scale, height / 2 - (ymin + ymax) / 2 * scale
    faces = [{"points": [(ox + p[0] * scale, oy + p[1] * scale, p[2]) for p in coords],
              "rgb": shade(face["colour"], face["points"])} for face, coords in zip(visible, mapped)]
    return png_bytes(rasterize_projected(faces, width, height, edge_depth_bias=1.5 / scale), width, height)
