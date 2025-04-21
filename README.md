# griffine

<img src="./images/griffine_logo_flattened_recolor.svg" width=300>

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

### Examples

```python
from affine import Affine
from griffine import Grid, Point, Tile

# 10m pixel grid in UTM coordinates
transform = Affine(10, 0, 200000, 0, -10, 6100000)

# First we create a grid!
grid = Grid(10000, 5000)

# We can tile the grid using another grid.
# In this example we'd get a 10x5 tile grid
# where each tile is a grid of 1000x1000.
tile_0_0 = grid.tile(Grid(10, 5))[0][0]
tile.size  # (1000, 1000)

# We can also add an affine transform to our grid.
# A transform allows converting between grid space and
# model space (i.e., cell coords and spatial coords).
affine_grid = grid.add_transform(transform)
affine_cell_0_0 = affine_grid[0][0]
affine_cell_0_0.origin  # Point(200000, 6100000)
affine_cell_0_0.centroid  # Point(200005, 6099995)
affine_cell_0_0.antiorigin  # Point(200010, 6099990)


# Grids can be tiled by a tile size instead of a grid.
# Here we'll get a 10x5 grid, but the left and bottom
# edge tiles will not be full size.
tiled_grid = grid.tile(Tile(1024, 1024))

# We can add a transform to a tiled grid too.
# Doing so gives us the ability to convert
# between tile coordinates and model space.
tiled_affine_grid = tiled_grid.add_transform(transform)
point = Point(
```

## How to say "griffine"

The name of this library is pronounced "grif-fine", as in the words "grift",
and "fine".
