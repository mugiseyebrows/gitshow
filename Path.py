
class Path:
    def __init__(self, points, color = None):
        self._color = color
        self._points = points
        self._commit = None
        self._parent = None
