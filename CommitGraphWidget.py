from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import QPointF, QRectF, Qt, QSizeF, QSize
from PyQt5.QtGui import QColor, QPen, QBrush, QTextOption
from Commit import Commit
from Path import Path
import datetime
import time

PAD_LEFT = 10
PAD_TOP = 10
COL_WIDTH = 18
ROW_HEIGHT = 18

class CommitGraphWidget(QtWidgets.QWidget):

    currentChanged = QtCore.pyqtSignal(str)

    def __init__(self, parent = None):
        super().__init__(parent)
        self._selected = None
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._showDate = False
        self._showTime = False
        self._showAuthor = False
        self.init([], [])
        
    def init(self, commits, paths):
        self.commits = commits
        self.paths = paths
        fm = QtGui.QFontMetrics(self.font())
        self._dateSize = fm.horizontalAdvance("2024-00-00") + 10
        self._timeSize = fm.horizontalAdvance("00:00:00") + 10
        self._authorSize = fm.averageCharWidth() * 25
        self._commitMessageSize = fm.averageCharWidth() * 80
        self._initTransform()

    def setShowDate(self, value):
        if self._showDate == value:
            return
        self._showDate = value
        self._initTransform()

    def setShowTime(self, value):
        if self._showTime == value:
            return
        self._showTime = value
        self._initTransform()

    def setShowAuthor(self, value):
        if self._showAuthor == value:
            return
        self._showAuthor = value
        self._initTransform()

    def _initTransform(self):

        x = PAD_LEFT
        if self._showDate:
            x += self._dateSize
        if self._showTime:
            x += self._timeSize
        if self._showAuthor:
            x += self._authorSize
        
        transform = QtGui.QTransform().translate(x, PAD_TOP).scale(COL_WIDTH, ROW_HEIGHT)
        inv_transform, _ = transform.inverted()
        self._transform = transform
        self._inv_transform = inv_transform
        self.resize(self.sizeHint())

    def selected(self):
        return self._selected
    
    def currentIndex(self):
        if self._selected is None:
            return
        for i, commit in enumerate(self.commits):
            if commit.sha == self._selected:
                return i

    def selectNext(self):
        if self._selected is None:
            return
        else:
            self.selectIndex(self.currentIndex() - 1)

    def selectPrev(self):
        if self._selected is None:
            return
        else:
            self.selectIndex(self.currentIndex() + 1)

    def selectIndex(self, y):

        if y < 0 or y >= len(self.commits):
            return

        sha = self.commits[y].sha
        if sha == self._selected:
            return
        self._selected = sha
        self.currentChanged.emit(sha)
        self.update()

    def mousePressEvent(self, event):
        point = self._inv_transform.map(event.pos())
        y = point.y()
        if y < 0:
            y = 0
        if y >= len(self.commits):
            y = len(self.commits) - 1
        self.selectIndex(y)
        return super().mousePressEvent(event)
    
    def sizeHint(self):
        if len(self.commits) == 0:
            return QSize(100, 100)
        point = self._transform.map(QPointF(5, self.commits[-1].y + 1))
        return QSize(int(point.x() + self._commitMessageSize), int(point.y()))

    def paintEvent(self, event):
        w = self.width() - 5 * 10
        
        painter = QtGui.QPainter(self)

        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        fm = QtGui.QFontMetricsF(self.font())
        
        commit: Commit

        commits = self.commits

        transform = self._transform

        white = QtGui.QColor(QtCore.Qt.GlobalColor.white)
        black = QtGui.QColor(QtCore.Qt.GlobalColor.black)
        red = QtGui.QColor(QtCore.Qt.GlobalColor.red)

        #print("paint event", event.rect(), event.region())

        if 0:
            ry1 = max(0, self._inv_transform.map(event.rect().topLeft()).y() - 50)
            ry2 = min(len(commits)-1, self._inv_transform.map(event.rect().bottomLeft()).y() + 50)
            commits_ = commits[ry1:ry2]
            shas = set([commit.sha for commit in commits_])

        # draw paths:
        t1 = time.time()
        path: Path
        for path in self.paths:
            """
            if path._commit not in shas and path._parent not in shas:
                continue
            """
            points = path._points
            painter.setPen(QtGui.QPen(QtGui.QColor(path._color), 2.0))
            for (x1, y1), (x2, y2) in zip(points, points[1:]):
                p1 = transform.map(QPointF(x1, y1))
                p2 = transform.map(QPointF(x2, y2))
                painter.drawLine(p1, p2)

        # draw circles
        t2 = time.time()
        painter.setPen(QtGui.QPen(white, 2.0))
        for commit in commits:
            painter.setBrush(QColor(commit.color))
            p = transform.map(QPointF(commit.x, commit.y))
            painter.drawEllipse(p, 5.0, 5.0)

        # draw commit message
        t3 = time.time()
        highlight = self.palette().color(QtGui.QPalette.ColorRole.Highlight)
        painter.setPen(QPen(black, 2.0))
        opt = QtGui.QTextOption(QtCore.Qt.AlignmentFlag.AlignCenter)
        for commit in commits:
            p = transform.map(QPointF(*commit.p2()) + QPointF(-0.2, -0.5))
            horizontalAdvance = fm.horizontalAdvance(commit.message_oneline)
            rect = QtCore.QRectF(p, QSizeF(horizontalAdvance + 10, ROW_HEIGHT))

            if self._selected == commit.sha:
                painter.fillRect(rect, highlight)
                painter.setPen(QPen(white, 2.0))
            else:
                painter.setPen(QPen(black, 2.0))

            painter.drawText(rect, commit.message_oneline, opt)

        season_colors = [
            "#f07167", # spring
            "#55a630", # summer
            "#f77f00", # autumn
            "#00b4d8", # winter
        ]

        seasons = [
            -1,3,3,0,0,0,1,1,1,2,2,2,3
        ]
        
        # draw date time and author
        t4 = time.time()
        opt = QtGui.QTextOption(QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignLeft)
        for commit in commits:
            p0 = transform.map(QPointF(*commit.p0()) + QPointF(-0.2, -0.5))
            x0 = p0.x()
            y0 = p0.y()
            if self._showDate:
                x0 -= self._dateSize
            if self._showTime:
                x0 -= self._timeSize
            if self._showAuthor:
                x0 -= self._authorSize

            if self._showDate:
                w = self._dateSize
                rect = QtCore.QRectF(QPointF(x0, y0), QSizeF(w, ROW_HEIGHT))
                date: datetime.datetime = commit.author_date.astimezone()
                color = season_colors[seasons[date.month]]
                painter.setPen(QColor(color))
                painter.drawText(rect, date.strftime("%Y-%m-%d"), opt)
                x0 += w
            
            painter.setPen(black)
            if self._showTime:
                w = self._timeSize
                rect = QtCore.QRectF(QPointF(x0, y0), QSizeF(w, ROW_HEIGHT))
                date: datetime.datetime = commit.author_date.astimezone()
                painter.drawText(rect, date.strftime("%H:%M:%S"), opt)
                x0 += w

            if self._showAuthor:
                w = self._authorSize
                rect = QtCore.QRectF(QPointF(x0, y0), QSizeF(w, ROW_HEIGHT))
                painter.drawText(rect, commit.author, opt)
                x0 += w

        t5 = time.time()

        #print("path {:.3f} circles {:.3f} message {:.3f} date time author {:.3f} s".format(t2 - t1, t3 - t2, t4 - t3, t5 - t4))

        # debug markers
        #markers = [(1, 22), (0, 26)]
        #markers = [(2, 31), (0, 35)]
        markers = []
        painter.setBrush(red)
        for marker in markers:
            p = transform.map(QPointF(*marker))
            painter.drawEllipse(p, 5.0, 5.0)

        super().paintEvent(event)

