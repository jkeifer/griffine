import pytest

from griffine import (
    Affine,
    Grid,
    Point,
)
from griffine.exceptions import (
    InvalidCoordinateError,
    InvalidGridError,
    InvalidTilingError,
    OutOfBoundsError,
)
from griffine.grid import Cell


@pytest.mark.parametrize(
    ('rows', 'cols'),
    [
        (10000, 5000),
        (1, 1),
    ],
)
def test_grid_constructor(rows: int, cols: int) -> None:
    _ = Grid(rows, cols)


@pytest.mark.parametrize(
    ('rows', 'cols'),
    [
        (0, 0),
        (-1, -1),
        (0, 1000),
        (100, -1343),
    ],
)
def test_grid_constructor_bad(rows: int, cols: int) -> None:
    with pytest.raises(InvalidGridError):
        Grid(rows, cols)


def test_grid_size() -> None:
    assert Grid(10000, 5000).size == (10000, 5000)


@pytest.mark.parametrize(
    ('row', 'col'),
    [
        (0, 0),
        (0, 1000),
        (1000, 0),
        (210134303, 20120404034),
    ],
)
def test_cell_constructor(row: int, col: int) -> None:
    _ = Cell(row, col)


@pytest.mark.parametrize(
    ('row', 'col'),
    [
        (-1, 0),
        (0, -1000),
        (-1000, -24),
    ],
)
def test_cell_constructor_bad(row: int, col: int) -> None:
    with pytest.raises(InvalidCoordinateError):
        Cell(row, col)


@pytest.mark.parametrize(
    'coords',
    [
        (5032, 42),
        (42, 4099),
        (0, 101),
        (101, 0),
        (0, 0),
        (-1, 1000),
        (0, -1000),
    ],
)
def test_grid_get_cell(coords: tuple[int, int]) -> None:
    rows, cols = 10000, 5000
    grid = Grid(rows, cols)
    cell = grid[coords]
    assert cell.row == coords[0] or cell.row == coords[0] + rows
    assert cell.col == coords[1] or cell.col == coords[1] + cols
    assert cell.parent_grid is grid


@pytest.mark.parametrize(
    'coords',
    [
        (10000, 42),
        (42, 5000),
        (-10001, 1000),
        (104300403, 0),
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
    ('coords', 'index'),
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
    linear_index = grid.linear_index(cell)
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
    assert tile1.size == (1024, 1024)
    cell1 = tile1[0, 0]
    assert cell1.row == 0
    assert cell1.col == 0
    assert cell1.tile_row == 0
    assert cell1.tile_col == 0
    tile2 = tiled[9, 4]
    assert tile2.row == 9
    assert tile2.col == 4
    assert tile2.rows == 784
    assert tile2.cols == 904
    assert tile2.size == (784, 904)
    cell2 = tile2[0, 0]
    assert cell2.row == 9216
    assert cell2.col == 4096
    assert cell1.tile_row == 0
    assert cell1.tile_col == 0


def test_grid_tile_into() -> None:
    grid = Grid(10000, 5000)
    tiled = grid.tile_into(Grid(10, 6))
    assert tiled.size == (10, 6)
    assert tiled.base_grid is grid
    assert tiled.tile_rows == 1000
    assert tiled.tile_cols == 834
    assert tiled.tile_size == (1000, 834)
    tile1 = tiled[0, 0]
    assert tile1.row == 0
    assert tile1.col == 0
    assert tile1.rows == 1000
    assert tile1.cols == 834
    assert tile1.size == (1000, 834)
    cell1 = tile1[0, 0]
    assert cell1.row == 0
    assert cell1.col == 0
    assert cell1.tile_row == 0
    assert cell1.tile_col == 0
    assert cell1.size == (1, 1)
    tile2 = tiled[9, 5]
    assert tile2.row == 9
    assert tile2.col == 5
    assert tile2.rows == 1000
    assert tile2.cols == 830
    cell2 = tile2[0, 0]
    assert cell2.row == 9000
    assert cell2.col == 4170
    assert cell1.tile_row == 0
    assert cell1.tile_col == 0


@pytest.mark.parametrize(
    'coords',
    [
        (4, 4),
        (0, 9),
        (12, 0),
    ],
)
def test_grid_tile_bad_coords(coords: tuple[int, int]) -> None:
    with pytest.raises(OutOfBoundsError):
        Grid(1, 1).tile_into(Grid(1, 1))[coords]


def test_affine_grid_ops() -> None:
    affine_grid = Grid(10, 5).add_transform(
        Affine(
            10,
            0,
            200000,
            0,
            -10,
            6100000,
        ),
    )
    assert affine_grid.width == 5 * 10
    assert affine_grid.height == 10 * -10
    assert affine_grid.origin == Point(200000, 6100000)
    assert affine_grid.centroid == Point(
        200000 + (affine_grid.width / 2),
        6100000 + (affine_grid.height / 2),
    )
    assert affine_grid.antiorigin == Point(
        200000 + affine_grid.width,
        6100000 + affine_grid.height,
    )
    origin = affine_grid.point_to_cell(affine_grid.origin)
    assert origin.row == 0
    assert origin.col == 0
    other = affine_grid.point_to_cell(Point(200048.9392, 6099934.3343))
    assert other.row == 6
    assert other.col == 4


def test_affine_grid_get_point_out_of_bounds() -> None:
    affine_grid = Grid(10, 5).add_transform(
        Affine(
            10,
            0,
            200000,
            0,
            -10,
            6100000,
        ),
    )
    with pytest.raises(OutOfBoundsError):
        affine_grid.point_to_cell(Point(5000, 5000))


@pytest.mark.parametrize(
    ('grid', 'tile_grid'),
    [
        ((4, 4), (3, 3)),
        ((9, 9), (8, 1)),
        ((12, 12), (12, 11)),
    ],
)
def test_tiling_error1(grid: tuple[int, int], tile_grid: tuple[int, int]) -> None:
    with pytest.raises(InvalidTilingError):
        Grid(*grid).tile_into(Grid(*tile_grid))


@pytest.mark.parametrize(
    ('grid', 'tile_size'),
    [
        ((4, 4), (5, 5)),
        ((4, 4), (8, 1)),
        ((4, 4), (1, 11)),
    ],
)
def test_tiling_error2(grid: tuple[int, int], tile_size: tuple[int, int]) -> None:
    with pytest.raises(InvalidTilingError):
        Grid(*grid).tile_via(Grid(*tile_size))


def test_tiled_affine_ops() -> None:
    transform = Affine(10, 0, 200000, 0, -10, 5100000)
    grid = Grid(10000, 5000)
    affine_grid = grid.add_transform(transform)
    point = Point(223433.2934, 5095752.8931)
    cell = affine_grid.point_to_cell(point)
    assert cell.row == 424
    assert cell.col == 2343
    tiled_affine_grid = affine_grid.tile_via(Grid(99, 1024))
    affine_tile = tiled_affine_grid.point_to_tile(point)
    assert affine_tile.row == 4
    assert affine_tile.col == 2
    affine_tile_cell = affine_tile.point_to_cell(point)
    assert affine_tile_cell.row == 424
    assert affine_tile_cell.col == 2343
    assert affine_tile_cell.tile_row == 4
    assert affine_tile_cell.tile_col == 2


def test_planar_area_grid_cell_and_tile() -> None:
    # 10m grid: each cell is 100 units squared.
    transform = Affine(10, 0, 200000, 0, -10, 6100000)
    grid = Grid(10, 5).add_transform(transform)
    assert grid.crs is None
    assert grid.area == 10 * 5 * 100
    assert grid[0, 0].area == 100.0

    tile = grid.tile_via(Grid(5, 5))[0, 0]
    assert tile.area == tile.rows * tile.cols * 100
    assert tile[0, 0].area == 100.0


def test_planar_area_uses_determinant_under_shear() -> None:
    # Sheared transform: per-cell area is |determinant| = |3*5 - 1*2| = 13.
    transform = Affine(3, 1, 0, 2, 5, 0)
    grid = Grid(2, 4).add_transform(transform)
    assert grid[0, 0].area == 13
    assert grid.area == 13 * 2 * 4


def test_geodesic_area_with_geographic_crs() -> None:
    pytest.importorskip('pyproj')
    # 100x100 grid of 0.1 degree cells, a 10x10 degree box from 50N down.
    transform = Affine(0.1, 0, -120, 0, -0.1, 50)
    grid = Grid(100, 100).add_transform(transform, crs=4326)

    assert grid.crs is not None
    assert grid.crs.is_geographic
    # A ~10x10 degree box near 45N is ~8.74e11 m^2 (the planar deg^2 value
    # would be 0.1 * 0.1 * 100 * 100 = 100, so this is unambiguously geodesic).
    assert grid.area == pytest.approx(8.74e11, rel=0.02)
    assert grid[0, 0].area == pytest.approx(7.98e7, rel=0.02)


def test_crs_and_geodesic_area_propagate_to_tiles_and_cells() -> None:
    pytest.importorskip('pyproj')
    transform = Affine(0.1, 0, -120, 0, -0.1, 50)
    tiled = Grid(100, 100).add_transform(transform, crs=4326).tile_via(Grid(10, 10))

    tile = tiled[0, 0]
    assert tile.crs is not None
    assert tile.crs.is_geographic
    assert tile.area == pytest.approx(8.06e9, rel=0.02)
    assert tile[0, 0].area == pytest.approx(7.98e7, rel=0.02)


def test_geographic_crs_via_tiled_grid_add_transform() -> None:
    pytest.importorskip('pyproj')
    # Adding a transform to an already-tiled grid: the transform describes the
    # tile grid, and the CRS must still reach the per-cell base grid.
    transform = Affine(1.0, 0, -120, 0, -1.0, 50)
    tiled = Grid(100, 100).tile_via(Grid(10, 10)).add_transform(transform, crs=4326)

    assert tiled.crs is not None
    assert tiled.crs.is_geographic
    assert tiled.base_grid.crs is not None
    cell = tiled[0, 0][0, 0]
    assert cell.crs is not None
    # Scaling the tile transform by 1/10 gives 0.1 degree cells at 50N, so the
    # geodesic cell area is ~7.98e7 m^2 (not the 0.1 * 0.1 planar deg^2 value)...
    assert cell.area == pytest.approx(7.98e7, rel=0.02)
    # ...and it matches the same cell computed on the underlying base grid.
    assert cell.area == pytest.approx(tiled.base_grid[0, 0].area)


def test_invalid_crs_fails_at_construction() -> None:
    exceptions = pytest.importorskip('pyproj.exceptions')
    with pytest.raises(exceptions.CRSError):
        Grid(1, 1).add_transform(Affine.identity(), crs='not-a-real-crs')
