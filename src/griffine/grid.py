from __future__ import annotations

import math

from typing import Annotated, Self

from affine import Affine

from griffine.types import (
    GridType,
    TileableType,
    TiledType,
    TransformableType,
)

NonNegativeInt = Annotated[int, ">=0"]
PositiveInt = Annotated[int, ">=1"]
Rows = Annotated[PositiveInt, "number of rows"]
Columns = Annotated[PositiveInt, "number of columns"]


def can_tile_into(grid_size: PositiveInt, tile_count: PositiveInt) -> bool:
    return tile_count == math.ceil(grid_size/math.ceil(grid_size/tile_count))


class Grid(TileableType, GridType):
    def _tiled(
        self,
        grid_size: tuple[Rows, Columns],
        tile_size: tuple[Rows, Columns],
    ) -> TiledType[Self]:
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
    ) -> TiledType[Self]:
        # TODO: move this logic to a constructor on TiledAffineGrid
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


class TiledGrid(TiledType, GridType):
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
        # TODO: move this logic to a constructor on TiledAffineGrid
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


class TiledAffineGrid(TiledType, TransformableType, GridType):
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
