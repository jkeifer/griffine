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


def can_tile_into(grid_size: PositiveInt, tile_count: PositiveInt) -> bool:
    return tile_count == math.ceil(grid_size/math.ceil(grid_size/tile_count))


class TileableType(GridType, Protocol):
    def _tiled(
        self,
        grid_size: tuple[Rows, Columns],
        tile_size: tuple[Rows, Columns],
    ) -> TiledType[Self]:
        raise NotImplementedError

    def tile_via(self, grid: GridType) -> TiledType[Self]:
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

    def tile_into(self, grid: GridType) -> TiledType[Self]:
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
class TiledType(Generic[T], GridType, Protocol):
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

    def __getitem__(
        self,
        coords: tuple[int, int],
    ) -> GridTile[Self]:
        row = coords[0] if coords[0] >= 0 else coords[0] + self.rows
        col = coords[1] if coords[1] >= 0 else coords[1] + self.cols

        if row < 0 or row >= self.rows:
            raise OutOfBoundsError('row outside grid')

        if col < 0 or col >= self.cols:
            raise OutOfBoundsError('column outside grid')

        # TODO: how to represent coords of tile cell in parent grid?
        return GridTile(
            row,
            col,
            self.tile_rows,
            self.tile_cols,
            self,
        )


class GridCell(CellType, Generic[T]):
    def __init__(
        self,
        row: NonNegativeInt,
        col: NonNegativeInt,
        grid: T,
    ) -> None:
        super().__init__(row=row, col=col)
        self.grid = grid

    @property
    def linear_index(self) -> NonNegativeInt:
        '''
        Find the index of the cell in the list of all cells in the grid,
        as would be given by reshaping the grid into a 1-d array of
        length rows * cols.
        '''
        return (self.grid.cols * self.row) + self.col


class GridTile(GridType, GridCell[T]):
    def __init__(
        self,
        row: NonNegativeInt,
        col: NonNegativeInt,
        rows: Rows,
        cols: Columns,
        grid: T,
    ) -> None:
        super().__init__(row=row, col=col, rows=rows, cols=cols, grid=grid)
