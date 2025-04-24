# griffine

[![build-status-image]][build-status]
[![coverage-status-image]][codecov]
[![pypi-version]][pypi]

<img src="./images/logo.svg" width=300>

Utilities for working with *gri*ds that have a*ffine* transforms, typically for
working with rasters or other gridded data.

## Installation

This package is distributed on pypi and can be `pip`-installed:

```commandline
pip install griffine
```

## Usage

This library is composed of several major classes:

* `Grid`
* `TiledGrid`
* `AffineGrid`
* `TiledAffineGrid`
* `Point`
* `Cell` and `AffineCell`
* `Tile` and `AffineTile`

`Grid` represents a two-dimensional grid of `Cell`s, with a size defined by its
`cols` and `rows`. A `TiledGrid` is, effectively, a grid of grids. Each cell in
a `TiledGrid` is a `Tile`. `Tiles` are both `Cell`s and `Grid`s, where the tile
grid is a subset of the larger `Grid` that has been tiled.

`AffineGrid` is a `Grid` with the addition of an affine transformation to allow
transformations between grid/image space and model space (in the case of
geospatial data, model space would be the raster's coordinate reference
system). `AffineGrids` allow looking up the `Point` represented by a `Cell`
(using its origin, centroid, or antiorigin), or the `Cell` containing a
`Point`.

A `TiledAffineGrid` is to an `AffineGrid` as a `TiledGrid` is to a `Grid`: each
`AffileTile` in a `TiledAffineGrid` is an `AffineGrid` representing some subset
of the larger `AffineGrid` that was tiled. `TiledAffineGrids` allow finding the
`AffineTile` containing` a `Cell` or a `Point`.

`griffine` does not handle coordinate systems and thus does not do any
reprojection. It is expected that users ensure they are using a consistent CRS
between the affine transforms of their grid and any points.

The [Python `__geo_interface__`
protocol](https://gist.github.com/sgillies/2217756) is supported by all
operations accepting a `Point` and on the `Point` class itself, to easily allow
using or casting to point geometries from other Python libraries (`shapely`,
`odc-geo`, etc.).
affine_grid = grid.add_transform(transform)affine_cell.antiorigin
### Examples

```python
# Affine re-exported from the affine package
# Point is re-exported from the pygeoif package
from griffine import Affine, Grid, Point

# 10m pixel grid in UTM coordinates
transform = Affine(10, 0, 200000, 0, -10, 5100000)

# First we create a grid!
grid = Grid(10000, 5000)

# We can grab a cell from the grid using index notation.
cell = grid[424, 2343]
cell.row  # 424
cell.col  # 2343

# We can tile the grid using another grid.
# In this example we'd get a 10x5 tile grid
# where each tile is a grid of 1000x1000.
tile = grid.tile_into(Grid(10, 5))[0, 0]
tile.size  # (1000, 1000)

# We can also add an affine transform to our grid.
# A transform allows converting between grid space and
# model space (i.e., cell coords and spatial coords).
affine_grid = grid.add_transform(transform)
affine_grid.origin      # Point(200000.0, 5100000.0)
affine_grid.centroid    # Point(225000.0, 5050000.0)
affine_grid.antiorigin  # Point(250000.0, 5000000.0)

# Affine grids also support grabbing a cell via
# index notation. Affine grids will provide affine
# cells, which support transform-based operations too.
affine_cell = affine_grid[0, 0]
affine_cell.origin      # Point(200000.0, 5100000.0)
affine_cell.centroid    # Point(200005.0, 5099995.0)
affine_cell.antiorigin  # Point(200010.0, 5099990.0)

# Transform operations can go the other way too.
# Let's make a point and find its enclosing cell!
point = Point(223433.2934, 5095752.8931)
affine_cell = affine_grid.point_to_cell(point)
affine_cell.row  # 424
affine_cell.col  # 2343

# Grids can also be tiled via a tile size expressed
# as a grid. Here we'll get a 10x5 tile grid, but the
# left and bottom edge tiles will not be full size.
tiled_affine_grid = affine_grid.tile_via(Grid(1024, 1024))

# Affine-enabled tiles and tile grids also support
# transform-based operations:
affine_tile = tiled_affine_grid.point_to_tile(point)
affine_tile.row  # 0
affine_tile.col  # 2
affine_tile_cell = affine_tile.point_to_cell(point)
affine_tile_cell.row  # 424
affine_tile_cell.col  # 2343
affine_tile_cell.tile_row  # 0
affine_tile_cell.tile_col  # 2

# We can work our way back up to the original grid
# from cells and tiles as needed:
#
#     cell          tile      tile grid    grid
affine_tile_cell.parent_grid.parent_grid.base_grid is affine_grid  # True
```

## How to say "griffine"

The name of this library is pronounced "grif-fine", as in the words "grift",
and "fine". It's also okay to say it "grif-feen", as rhymes with "mean".

[build-status-image]: https://github.com/jkeifer/griffine/actions/workflows/ci.yml/badge.svg
[build-status]: https://github.com/jkeifer/griffine/actions/workflows/ci.yml
[coverage-status-image]: https://img.shields.io/codecov/c/github/jkeifer/griffine/main.svg
[codecov]: https://codecov.io/github/jkeifer/griffine?branch=main
[pypi-version]: https://img.shields.io/pypi/v/griffine.svg
[pypi]: https://pypi.org/project/griffine/
