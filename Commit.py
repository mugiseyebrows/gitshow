class Commit:
    def __init__(self, sha):
        self.sha = sha
        self.parent = []
        self.author = None
        self.committer = None
        self._message = []
        self.gpgsig = []
        self.x = None
        self.x2 = None
        self.y = None
        self.color = None
    
    def p(self):
        return self.x, self.y

    def p2(self):
        if self.x2 is None:
            return self.p()
        return self.x2, self.y

    def __repr__(self):
        return "Commit(p={}, sha={}, message={}, )".format(self.p(), self.sha, self._message)
