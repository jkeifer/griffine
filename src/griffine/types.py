from __future__ import annotations

import math

from abc import abstractmethod
from typing import (
    TYPE_CHECKING,
    Annotated,
    Protocol,
    TypeAlias,
    TypeVar,
    runtime_checkable,
)

from affine import Affine
from pygeoif import Point, shape
from pygeoif.types import GeoType

from griffine.exceptions import (
    InvalidCoordinateError,
    InvalidGridError,
    InvalidTilingError,
    OutOfBoundsError,
)

if TYPE_CHECKING:
    from pyproj import CRS

# A CRS may be associated with a transform as a pyproj.CRS or anything
# pyproj.CRS.from_user_input understands (e.g. an EPSG int or a string).
CRSInput: TypeAlias = 'CRS | str | int'

NonNegativeInt = Annotated[int, '>=0']
PositiveInt = Annotated[int, '>=1']
Rows = Annotated[PositiveInt, 'number of rows']
Columns = Annotated[PositiveInt, 'number of columns']
GridSize: TypeAlias = tuple[Rows, Columns]

GT = TypeVar('GT', bound='GridType')
GT_cov = TypeVar('GT_cov', bound='GridType', covariant=True)


# FUTURE: validation via automatic coercion into a Point type
PointGeoType = Annotated[GeoType, 'geom type is point']


@runtime_checkable
class CellType(Protocol):
    row: NonNegativeInt
    col: NonNegativeInt

    def __init__(
        self,
        row: NonNegativeInt,
        col: NonNegativeInt,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        if row < 0:
            raise InvalidCoordinateError('cell row must be 0 or greater')

        if col < 0:
            raise InvalidCoordinateError('cell col must be 0 or greater')

        self.row = row
        self.col = col

    @property
    def size(self) -> GridSize:
        return (1, 1)


@runtime_checkable
class TiledCellType(CellType, Protocol):
    parent_grid: GridTileType
    tile_row: NonNegativeInt
    tile_col: NonNegativeInt

    def __init__(
        self,
        tile_row: NonNegativeInt,
        tile_col: NonNegativeInt,
        parent_grid: GridTileType,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.tile_row = tile_row
        self.tile_col = tile_col
        self.parent_grid = parent_grid


def realize_crs(crs: CRSInput | None) -> CRS | None:
    """Parse `crs` into a `pyproj.CRS`, or return None if `crs` is None.

    Importing pyproj is deferred to here so the optional `crs` extra is only
    required when a CRS is actually associated with a transform.
    """
    if crs is None:
        return None

    try:
        from pyproj import CRS
    except ModuleNotFoundError as e:  # pragma: no cover
        raise ImportError(
            "associating a CRS requires the 'crs' extra: pip install 'griffine[crs]'",
        ) from e

    return CRS.from_user_input(crs)


def planar_area(transform: Affine, size: GridSize) -> float:
    """Planar area of `size` cells under `transform`, in its own units squared.

    Because it derives from the transform's determinant, it is correct for
    any transfrom in any projected CRS, even under rotation or shear.
    """
    rows, cols = size
    return abs(transform.determinant) * rows * cols


def geodesic_area(
    transform: Affine,
    size: GridSize,
    crs: CRS,
) -> float:
    """Geodesic area of `size` cells under `transform`, in square meters.

    Computed on `crs`'s ellipsoid; `crs` must be geographic. For geographic
    grids this differs significantly from (and is usually more useful than)
    the planar area in square degrees.
    """
    rows, cols = size
    # Corners in grid space, traced around the cell footprint.
    corners = ((0, 0), (cols, 0), (cols, rows), (0, rows))
    lons, lats = zip(*(transform * corner for corner in corners), strict=True)

    geod = crs.get_geod()
    if geod is None:
        raise RuntimeError(f'geographic CRS {crs} unexpectedly has no ellipsoid')

    area, _ = geod.polygon_area_perimeter(lons, lats)
    return abs(area)


@runtime_checkable
class TransformableType(Protocol):
    transform: Affine
    crs: CRS | None
    area: float

    def __init__(
        self,
        transform: Affine,
        crs: CRSInput | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.transform = transform
        self.crs = realize_crs(crs)

        if self.crs is not None and self.crs.is_geographic:
            self.area = geodesic_area(self.transform, self.size, self.crs)
        else:
            self.area = planar_area(self.transform, self.size)

    @property
    @abstractmethod
    def size(self) -> GridSize:  # pragma: no cover
        raise NotImplementedError

    @property
    def width(self) -> int:
        return self.transform.a * self.size[1]

    @property
    def height(self) -> int:
        return self.transform.e * self.size[0]

    @property
    def origin(self) -> Point:
        return Point(*(self.transform * (0, 0)))

    @property
    def centroid(self) -> Point:
        coords = (x / 2 for x in self.size[::-1])
        return Point(*(self.transform * coords))

    @property
    def antiorigin(self) -> Point:
        return Point(*(self.transform * self.size[::-1]))


@runtime_checkable
class AffineTiledGridCellType(
    TiledCellType,
    TransformableType,
    Protocol,
): ...


CT_cov = TypeVar('CT_cov', bound=CellType, covariant=True)


@runtime_checkable
class GridType(Protocol[CT_cov]):
    rows: Rows
    cols: Columns

    def __init__(
        self,
        rows: Rows,
        cols: Columns,
        **kwargs,
    ) -> None:
        if rows < 1:
            raise InvalidGridError('grid rows must be 1 or greater')

        if cols < 1:
            raise InvalidGridError('grid cols must be 1 or greater')

        # Assign before delegating to super so that `size` is available to
        # deeper mixins during construction (e.g. TransformableType computes
        # its area eagerly and needs `size`).
        self.rows = rows
        self.cols = cols

        super().__init__(**kwargs)

    @property
    def size(self) -> GridSize:
        return self.rows, self.cols

    def linear_index(self, cell: CellType) -> NonNegativeInt:
        return (self.cols * cell.row) + cell.col

    @abstractmethod
    def _get_cell(
        self,
        row: NonNegativeInt,
        col: NonNegativeInt,
    ) -> CT_cov:  # pragma: no cover
        raise NotImplementedError

    def __getitem__(
        self,
        coords: tuple[int, int],
    ) -> CT_cov:
        row = coords[0] if coords[0] >= 0 else coords[0] + self.rows
        col = coords[1] if coords[1] >= 0 else coords[1] + self.cols

        if row < 0 or row >= self.rows:
            raise OutOfBoundsError('row outside grid')

        if col < 0 or col >= self.cols:
            raise OutOfBoundsError('column outside grid')

        return self._get_cell(row, col)


GTT_cov = TypeVar('GTT_cov', bound='GridTileType', covariant=True)


@runtime_checkable
class TiledGridType(GridType[GTT_cov], Protocol[GT, GTT_cov]):
    base_grid: GT
    tile_rows: Rows
    tile_cols: Columns

    def __init__(
        self,
        tile_rows: Rows,
        tile_cols: Columns,
        base_grid: GT,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        if tile_rows < 1:
            raise InvalidGridError('tile grid rows must be 1 or greater')

        if tile_cols < 1:
            raise InvalidGridError('tile grid cols must be 1 or greater')

        self.tile_rows = tile_rows
        self.tile_cols = tile_cols
        self.base_grid = base_grid

    @property
    def tile_size(self) -> GridSize:
        return self.tile_rows, self.tile_cols

    @abstractmethod
    def _get_cell(
        self,
        row: NonNegativeInt,
        col: NonNegativeInt,
    ) -> GTT_cov:  # pragma: no cover
        raise NotImplementedError

    def __getitem__(
        self,
        coords: tuple[int, int],
    ) -> GTT_cov:
        # If coords are negative coerce to a non-negative equivalent
        # e.g., -1 is equivalent to the value given by len(self) - 1
        row = coords[0] if coords[0] >= 0 else coords[0] + self.rows
        col = coords[1] if coords[1] >= 0 else coords[1] + self.cols

        if row < 0 or row >= self.rows:
            raise OutOfBoundsError('row outside grid')

        if col < 0 or col >= self.cols:
            raise OutOfBoundsError('column outside grid')

        return self._get_cell(
            row,
            col,
        )

    def tile_coords_to_base_coords(
        self,
        row: NonNegativeInt,
        col: NonNegativeInt,
        tile_row: NonNegativeInt,
        tile_col: NonNegativeInt,
    ) -> tuple[NonNegativeInt, NonNegativeInt]:
        return (
            (tile_row * self.tile_rows) + row,
            (tile_col * self.tile_cols) + col,
        )


AGTT_cov = TypeVar('AGTT_cov', bound='AffineGridTileType', covariant=True)


@runtime_checkable
class TransformableGridType(
    GridType[CT_cov],
    TransformableType,
    Protocol[CT_cov],
):
    def _point_to_coords(
        self,
        point: PointGeoType,
    ) -> tuple[NonNegativeInt, NonNegativeInt]:
        _point = shape(point) if not isinstance(point, Point) else point
        # ignoring type error until affine v3.0 is officially released
        col, row = map(
            math.floor,
            ~self.transform * (_point.x, _point.y),  # type: ignore
        )
        return row, col


@runtime_checkable
class TransformableTiledGridType(
    TiledGridType[GT, GTT_cov],
    TransformableGridType[GTT_cov],
    Protocol[GT, GTT_cov],
): ...


@runtime_checkable
class TileType(GridType[CT_cov], CellType, Protocol[CT_cov]):
    def __init__(
        self,
        row: NonNegativeInt,
        col: NonNegativeInt,
        rows: Rows,
        cols: Columns,
        **kwargs,
    ) -> None:
        super().__init__(row=row, col=col, rows=rows, cols=cols, **kwargs)


@runtime_checkable
class GridTileType(TileType[CT_cov], Protocol[CT_cov]):
    parent_grid: TiledGridType

    def __init__(
        self,
        row: NonNegativeInt,
        col: NonNegativeInt,
        parent_grid: TiledGridType,
        **kwargs,
    ) -> None:
        # If tile is on the right and/or bottom edge, the size might
        # not be the same as indicated by the nominal tile dimensions
        tile_rows = parent_grid.tile_rows
        tile_cols = parent_grid.tile_cols
        rows = min(tile_rows, parent_grid.base_grid.rows - (row * tile_rows))
        cols = min(tile_cols, parent_grid.base_grid.cols - (col * tile_cols))

        super().__init__(row=row, col=col, rows=rows, cols=cols, **kwargs)
        self.parent_grid = parent_grid

    def tile_coords_to_base_coords(
        self,
        row: NonNegativeInt,
        col: NonNegativeInt,
    ) -> tuple[NonNegativeInt, NonNegativeInt]:
        return self.parent_grid.tile_coords_to_base_coords(row, col, self.row, self.col)


@runtime_checkable
class AffineGridTileType(
    GridTileType[CT_cov],
    TransformableGridType,
    Protocol[CT_cov],
):
    def __init__(
        self,
        row: NonNegativeInt,
        col: NonNegativeInt,
        parent_grid: TransformableTiledGridType,
        **kwargs,
    ) -> None:
        super().__init__(
            row=row,
            col=col,
            parent_grid=parent_grid,
            transform=parent_grid.base_grid.transform
            * Affine.translation(
                *parent_grid.tile_coords_to_base_coords(0, 0, row, col)[::-1],
            ),
            crs=parent_grid.crs,
            **kwargs,
        )


TGT_cov = TypeVar('TGT_cov', bound=TiledGridType, covariant=True)


def can_tile_into(grid_size: PositiveInt, tile_count: PositiveInt) -> bool:
    return tile_count == math.ceil(grid_size / math.ceil(grid_size / tile_count))


@runtime_checkable
class TileableType(GridType[CT_cov], Protocol[CT_cov, TGT_cov]):
    @abstractmethod
    def _tiled(
        self,
        grid_size: GridSize,
        tile_size: GridSize,
    ) -> TGT_cov:  # pragma: no cover
        raise NotImplementedError

    def tile_via(self, grid: GridType) -> TGT_cov:
        """Tile self where each tile is the size of `grid`."""
        if self.cols < grid.cols or self.rows < grid.rows:
            raise InvalidTilingError(
                f'Cannot tile grid of size {self.size} with tiles of size {grid.size}',
            )

        rows = math.ceil(self.rows / grid.rows)
        cols = math.ceil(self.cols / grid.cols)

        return self._tiled(
            (rows, cols),
            grid.size,
        )

    def tile_into(self, grid: GridType) -> TGT_cov:
        """Tile self into the tile grid is given by `grid`."""
        if not (
            can_tile_into(self.rows, grid.rows) and can_tile_into(self.cols, grid.cols)
        ):
            raise InvalidTilingError(
                f'Cannot tile grid of size {self.size} into grid {grid.size}',
            )

        tile_rows = math.ceil(self.rows / grid.rows)
        tile_cols = math.ceil(self.cols / grid.cols)

        return self._tiled(
            grid.size,
            (tile_rows, tile_cols),
        )
