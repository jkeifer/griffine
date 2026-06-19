# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [0.2.0] - 2026-06-19

### Added

- `area` on affine grids, tiles, and cells. Without a CRS it is the planar area
  in the transform's own units squared (derived from the transform determinant,
  so correct under rotation/shear).
- Optional association of a CRS with a transform via `add_transform(transform,
  crs=...)`. When the CRS is geographic, `area` is computed geodesically (in
  square meters) on the CRS's ellipsoid. Requires the new optional `crs` extra
  (`pip install 'griffine[crs]'`, which pulls in `pyproj`).
- `GridSize` type alias and the `realize_crs`, `planar_area`, and
  `geodesic_area` helpers.

### Changed

- The misspelled `heigth` property was renamed to the correct `height`. It is
  defined on `TransformableType` and inherited by every concrete transformable:
  `AffineGrid`, `TiledAffineGrid`, `AffineGridCell`, `TiledAffineGridCell`, and
  `AffineGridTile`.

## [0.1.0] - 2025-04-24

Initial release 🎉

[unreleased]: https://github.com/jkeifer/griffine/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/jkeifer/griffine/releases/tag/v0.2.0
[0.1.0]: https://github.com/jkeifer/griffine/releases/tag/v0.1.0
