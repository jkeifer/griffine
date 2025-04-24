from __future__ import annotations

from affine import Affine

from griffine.types import (
    AffineGridTileType,
    CellType,
    Columns,
    GridTileType,
    GridType,
    NonNegativeInt,
    PointGeoType,
    Rows,
    TileableType,
    TiledCellType,
    TiledGridType,
    TileType,
    TransformableGridType,
    TransformableTiledGridType,
    TransformableType,
)


class Grid(TileableType['GridCell', 'TiledGrid']):
    def _get_cell(self, row: NonNegativeInt, col: NonNegativeInt) -> GridCell:
        return GridCell(row=row, col=col, parent_grid=self)

    def _tiled(
        self,
        grid_size: tuple[Rows, Columns],
        tile_size: tuple[Rows, Columns],
    ) -> TiledGrid:
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


class AffineGrid(
    TileableType['AffineGridCell', 'TiledAffineGrid'],
    TransformableGridType,
):
    def __init__(self, rows: Rows, cols: Columns, transform: Affine) -> None:
        super().__init__(rows=rows, cols=cols, transform=transform)

    def _get_cell(self, row: NonNegativeInt, col: NonNegativeInt) -> AffineGridCell:
        return AffineGridCell(row=row, col=col, parent_grid=self)

    def _tiled(
        self,
        grid_size: tuple[Rows, Columns],
        tile_size: tuple[Rows, Columns],
    ) -> TiledAffineGrid:
        return TiledAffineGrid(
            rows=grid_size[0],
            cols=grid_size[1],
            tile_rows=tile_size[0],
            tile_cols=tile_size[1],
            base_grid=self,
            transform=self.transform * Affine.scale(tile_size[1], tile_size[0]),
        )

    def point_to_cell(
        self,
        point: PointGeoType,
    ) -> AffineGridCell:
        return self[self._point_to_coords(point)]


class TiledGrid(TiledGridType[Grid, 'GridTile']):
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

    def _get_cell(self, row: NonNegativeInt, col: NonNegativeInt) -> GridTile:
        return GridTile(row=row, col=col, parent_grid=self)

    def add_transform(self, transform: Affine) -> TiledAffineGrid:
        base = self.base_grid.add_transform(
            transform
            * Affine.scale(
                1 / self.tile_cols,
                1 / self.tile_rows,
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


class TiledAffineGrid(
    TransformableTiledGridType[AffineGrid, 'AffineGridTile'],
):
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

    def _get_cell(
        self,
        row: NonNegativeInt,
        col: NonNegativeInt,
    ) -> AffineGridTile:
        return AffineGridTile(row=row, col=col, parent_grid=self)

    def point_to_tile(
        self,
        point: PointGeoType,
    ) -> AffineGridTile:
        return self[self._point_to_coords(point)]

    def point_to_cell(
        self,
        point: PointGeoType,
    ) -> TiledAffineGridCell:
        tile = self.point_to_tile(point)
        return tile.point_to_cell(point)


class Cell(CellType):
    def __init__(self, row: NonNegativeInt, col: NonNegativeInt) -> None:
        super().__init__(row=row, col=col)


class GridCell(CellType):
    def __init__(
        self,
        row: NonNegativeInt,
        col: NonNegativeInt,
        parent_grid: GridType,
    ) -> None:
        super().__init__(row=row, col=col)
        self.parent_grid = parent_grid


class TiledGridCell(TiledCellType):
    def __init__(
        self,
        row: NonNegativeInt,
        col: NonNegativeInt,
        tile_row: NonNegativeInt,
        tile_col: NonNegativeInt,
        parent_grid: GridTileType,
    ) -> None:
        super().__init__(
            row=row,
            col=col,
            tile_row=tile_row,
            tile_col=tile_col,
            parent_grid=parent_grid,
        )


class AffineGridCell(CellType, TransformableType):
    def __init__(
        self,
        row: NonNegativeInt,
        col: NonNegativeInt,
        parent_grid: TransformableGridType,
    ) -> None:
        super().__init__(
            row=row,
            col=col,
            transform=parent_grid.transform * Affine.translation(col, row),
        )
        self.parent_grid = parent_grid


class TiledAffineGridCell(
    TiledCellType,
    TransformableType,
):
    def __init__(
        self,
        row: NonNegativeInt,
        col: NonNegativeInt,
        tile_row: NonNegativeInt,
        tile_col: NonNegativeInt,
        parent_grid: AffineGridTileType,
    ) -> None:
        super().__init__(
            row=row,
            col=col,
            tile_row=tile_row,
            tile_col=tile_col,
            parent_grid=parent_grid,
            transform=parent_grid.transform * Affine.translation(col, row),
        )


class Tile(TileType[GridCell]):
    def __init__(
        self,
        row: NonNegativeInt,
        col: NonNegativeInt,
        rows: Rows,
        cols: Columns,
    ) -> None:
        super().__init__(row=row, col=col, rows=rows, cols=cols)

    def _get_cell(self, row: NonNegativeInt, col: NonNegativeInt) -> GridCell:
        return GridCell(row=row, col=col, parent_grid=self)


class GridTile(GridTileType[TiledGridCell]):
    def __init__(
        self,
        row: NonNegativeInt,
        col: NonNegativeInt,
        parent_grid: TiledGridType,
    ) -> None:
        super().__init__(
            row=row,
            col=col,
            parent_grid=parent_grid,
        )

    def _get_cell(self, row: NonNegativeInt, col: NonNegativeInt) -> TiledGridCell:
        row, col = self.tile_coords_to_parent_coords(row, col)
        return TiledGridCell(
            row=row,
            col=col,
            tile_row=self.row,
            tile_col=self.col,
            parent_grid=self,
        )


class AffineGridTile(AffineGridTileType[TiledAffineGridCell]):
    def __init__(
        self,
        row: NonNegativeInt,
        col: NonNegativeInt,
        parent_grid: TransformableTiledGridType,
    ) -> None:
        super().__init__(
            row=row,
            col=col,
            parent_grid=parent_grid,
        )

    def _get_cell(
        self,
        row: NonNegativeInt,
        col: NonNegativeInt,
    ) -> TiledAffineGridCell:
        row, col = self.tile_coords_to_parent_coords(row, col)
        return TiledAffineGridCell(
            row=row,
            col=col,
            tile_row=self.row,
            tile_col=self.col,
            parent_grid=self,
        )

    def point_to_cell(
        self,
        point: PointGeoType,
    ) -> TiledAffineGridCell:
        return self[self._point_to_coords(point)]
