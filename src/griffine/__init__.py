from .exceptions import OutOfBoundsError
from .grid import Affine, Grid

try:
    from .__version__ import __version__, __version_tuple__
except ImportError:
    __version__ = "0.0.0"
    __version_tuple__ = ("0", "0", "0")

__all__: list[str] = [
    "Affine",
    "Grid",
    "OutOfBoundsError",
    "__version__",
    "__version_tuple__",
]
