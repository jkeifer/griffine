import pytest

from griffine import (
    Affine,
    Grid,
    OutOfBoundsError,
)


@pytest.mark.parametrize(
    'rows,cols',
    [
        (10000, 5000),
        (1, 1),
        #(0, 0),
        #(-1, -1),
        #(0, 1000),
    ],
)
def test_grid_constructor(rows: int, cols: int) -> None:
    _ = Grid(rows, cols)


def test_grid_size() -> None:
    assert Grid(10000, 5000).size == (10000, 5000)


@pytest.mark.parametrize(
    'coords',
    [
        (5032, 42),
        (42, 4099),
        #(0, 101),
        #(101, 0),
        #(0, 0),
        (-1, 1000),
        #(0, -1000),
    ],
)
def test_grid_get_cell(coords: tuple[int, int]) -> None:
    rows, cols = 10000, 5000
    grid = Grid(rows, cols)
    cell = grid[coords]
    assert cell.row == coords[0] or cell.row == coords[0] + rows
    assert cell.col == coords[1] or cell.col == coords[1] + cols
    assert cell.grid is grid


@pytest.mark.parametrize(
    'coords',
    [
        (10000, 42),
        (42, 5000),
        (-10001, 1000),
        #(104300403, 0),
    ],
)
def test_grid_get_cell_bad_index(coords: tuple[int, int]) -> None:
    grid = Grid(10000, 5000)
    with pytest.raises(OutOfBoundsError):
        grid[coords]


def test_grid_add_transform() -> None:
    grid = Grid(10000, 5000)
    transform = Affine(10, 0, 200000, 0, -10, 6100000)
    _ = grid.add_transform(transform)


@pytest.mark.parametrize(
    'coords,index',
    [
        ((0, 0), 0),
        ((9, 9), 99),
        ((4, 9), 49),
        ((5, 0), 50),
        ((0, 5), 5),
    ],
)
def test_grid_cell_linear_index(
    coords: tuple[int, int],
    index: int,
) -> None:
    rows, cols = 10, 10
    grid = Grid(rows, cols)
    cell = grid[coords]
    linear_index = cell.linear_index
    assert linear_index == index


def test_grid_tile_via() -> None:
    grid = Grid(10000, 5000)
    tiled = grid.tile_via(Grid(1024, 1024))
    assert tiled.base_grid is grid
    assert tiled.tile_rows == 1024
    assert tiled.tile_cols == 1024
    assert tiled.tile_size == (1024, 1024)
    tile1 = tiled[0, 0]
    assert tile1.row == 0
    assert tile1.col == 0
    assert tile1.rows == 1024
    assert tile1.cols == 1024
    cell1 = tile1[0, 0]
    assert cell1.row == 0
    assert cell1.col == 0
    tile2 = tiled[9, 4]
    assert tile2.row == 9
    assert tile2.col == 4
    assert tile2.rows == 1000
    assert tile2.cols == 1000
    cell2 = tile2[0, 0]
    assert cell2.row == 0
    assert cell2.col == 0

