from __future__ import annotations

import math

from typing import Annotated, Generic, Protocol, Self, TypeVar, runtime_checkable

from affine import Affine

from griffine.exceptions import (
    InvalidCoordinateError,
    InvalidGridError,
    InvalidTilingError,
    OutOfBoundsError,
)

NonNegativeInt = Annotated[int, ">=0"]
PositiveInt = Annotated[int, ">=1"]
Rows = Annotated[PositiveInt, "number of rows"]
Columns = Annotated[PositiveInt, "number of columns"]


@runtime_checkable
class CellType(Protocol):
    row: NonNegativeInt
    col: NonNegativeInt

    def __init__(
        self,
        row: NonNegativeInt,
        col: NonNegativeInt,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)

        if row < 0:
            raise InvalidCoordinateError('cell row must be 0 or greater')

        if col < 0:
            raise InvalidCoordinateError('cell col must be 0 or greater')

        self.row = row
        self.col = col


@runtime_checkable
class GridType(Protocol):
    rows: Rows
    cols: Columns

    def __init__(
        self,
        rows: Rows,
        cols: Columns,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)

        if rows < 1:
            raise InvalidGridError('grid rows must be 1 or greater')

        if cols < 1:
            raise InvalidGridError('grid cols must be 1 or greater')

        self.rows = rows
        self.cols = cols

    @property
    def size(self) -> tuple[Rows, Columns]:
        return self.rows, self.cols

    def __getitem__(
        self,
        coords: tuple[int, int],
    ) -> GridCell[Self]:
        row = coords[0] if coords[0] >= 0 else coords[0] + self.rows
        col = coords[1] if coords[1] >= 0 else coords[1] + self.cols

        if row < 0 or row >= self.rows:
            raise OutOfBoundsError('row outside grid')

        if col < 0 or col >= self.cols:
            raise OutOfBoundsError('column outside grid')

        return GridCell(row, col, self)


@runtime_checkable
class TransformableType(Protocol):
    transform: Affine

    def __init__(
        self,
        transform: Affine,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.transform = transform


T = TypeVar('T', bound=GridType)


class GridCell(CellType, Generic[T]):
    def __init__(
        self,
        row: NonNegativeInt,
        col: NonNegativeInt,
        grid: T,
    ) -> None:
        super().__init__(row=row, col=col)
        self.grid = grid


class GridTile(GridType, GridCell[T]):
    def __init__(
        self,
        row: NonNegativeInt,
        col: NonNegativeInt,
        rows: Rows,
        cols: Columns,
        grid: T,
    ) -> None:
        super().__init__(row=row, col=col, rows=rows, cols=cols)
        self.grid = grid


def can_tile_into(grid_size: PositiveInt, tile_count: PositiveInt) -> bool:
    return tile_count == math.ceil(grid_size/math.ceil(grid_size/tile_count))


class TileableType(GridType, Protocol):
    def _tiled(
        self,
        grid_size: tuple[Rows, Columns],
        tile_size: tuple[Rows, Columns],
    ) -> Tiled[Self]:
        raise NotImplementedError

    def tile_via(self, grid: Grid) -> Tiled[Self]:
        '''Tile self where each tile is the size of `grid`.'''
        ...
        if (
            self.cols < grid.cols
            or self.rows < grid.rows
        ):
            raise InvalidTilingError(
                f'Cannot tile grid of size {self.size} with tiles of size {grid.size}',
            )

        rows = math.ceil(self.rows / grid.rows)
        cols = math.ceil(self.cols / grid.cols)

        return self._tiled(
            (rows, cols),
            grid.size,
        )

    def tile_into(self, grid: GridType) -> Tiled[Self]:
        '''Tile self into the tile grid is given by `grid`.'''
        ...
        if not (
            can_tile_into(self.rows, grid.rows)
            and can_tile_into(self.cols, grid.cols)
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


@runtime_checkable
class Tiled(Generic[T], Protocol):
    base_grid: T
    tile_rows: Rows
    tile_cols: Columns

    def __init__(
        self,
        base_grid: T,
        tile_rows: Rows,
        tile_cols: Columns,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)

        if tile_rows < 1:
            raise InvalidGridError('tile grid rows must be 1 or greater')

        if tile_cols < 1:
            raise InvalidGridError('tile grid cols must be 1 or greater')

        self.base_grid = base_grid
        self.tile_rows = tile_rows
        self.tile_cols = tile_cols

    @property
    def tile_size(self) -> tuple[Rows, Columns]:
        return self.tile_rows, self.tile_cols


class Grid(TileableType, GridType):
    def _tiled(
        self,
        grid_size: tuple[Rows, Columns],
        tile_size: tuple[Rows, Columns],
    ) -> Tiled[Self]:
        return TiledGrid(
            rows=grid_size[0],
            cols=grid_size[1],
            tile_rows=tile_size[0],
            tile_cols=tile_size[1],
            base_grid=self,
        )

    def add_transform(self, transform: Affine) -> AffineGrid:
        return AffineGrid(
            self.rows,
            self.cols,
            transform,
        )


class AffineGrid(TransformableType, TileableType, GridType):
    def __init__(self, rows: Rows, cols: Columns, transform: Affine) -> None:
        super().__init__(rows=rows, cols=cols, transform=transform)

    def _tiled(
        self,
        grid_size: tuple[Rows, Columns],
        tile_size: tuple[Rows, Columns],
    ) -> Tiled[Self]:
        return TiledAffineGrid(
            rows=grid_size[0],
            cols=grid_size[1],
            tile_rows=tile_size[0],
            tile_cols=tile_size[1],
            base_grid=self,
            transform=Affine(
                self.transform.a * tile_size[0],
                self.transform.b,
                self.transform.c,
                self.transform.d,
                self.transform.e * tile_size[1],
                self.transform.f,
            ),
        )


class TiledGrid(Tiled, GridType):
    def __init__(
        self,
        rows: Rows,
        cols: Columns,
        tile_rows: Rows,
        tile_cols: Columns,
        base_grid: Grid,
    ) -> None:
        super().__init__(
            rows=rows,
            cols=cols,
            tile_rows=tile_rows,
            tile_cols=tile_cols,
            base_grid=base_grid,
        )

    def add_transform(self, transform: Affine) -> TiledAffineGrid:
        base = self.base_grid.add_transform(
            Affine(
                transform.a / self.tile_cols,
                transform.b,
                transform.c,
                transform.d,
                transform.e / self.tile_rows,
                transform.f,
            ),
        )
        return TiledAffineGrid(
            self.rows,
            self.cols,
            self.tile_rows,
            self.tile_cols,
            base,
            transform,
        )


class TiledAffineGrid(Tiled, TransformableType, GridType):
    def __init__(
        self,
        rows: Rows,
        cols: Columns,
        tile_rows: Rows,
        tile_cols: Columns,
        base_grid: AffineGrid,
        transform: Affine,
    ) -> None:
        super().__init__(
            rows=rows,
            cols=cols,
            tile_rows=tile_rows,
            tile_cols=tile_cols,
            base_grid=base_grid,
            transform=transform,
        )
    # TODO: need to make sure base grid gets appropriate transform?
