# imghdr.py - backport simple para Python 3.13+
def what(file, h=None):
    if h is None:
        with open(file, 'rb') as f:
            h = f.read(32)
    if h.startswith(b'\211PNG\r\n\032\n'):
        return 'png'
    if h[6:10] in (b'JFIF', b'Exif'):
        return 'jpeg'
    if h.startswith(b'GIF87a') or h.startswith(b'GIF89a'):
        return 'gif'
    if h.startswith((b'II*\x00', b'MM\x00*')):
        return 'tiff'
    if h.startswith(b'BM'):
        return 'bmp'
    return None
