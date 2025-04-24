class GriffineError(Exception):
    pass


class OutOfBoundsError(IndexError, GriffineError):
    pass


class InvalidCoordinateError(ValueError, GriffineError):
    pass


class InvalidGridError(ValueError, GriffineError):
    pass


class InvalidTilingError(InvalidGridError):
    pass
