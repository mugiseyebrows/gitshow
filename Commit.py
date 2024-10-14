class Commit:
    def __init__(self, sha, sha_short = None):
        self.sha = sha
        self.sha_short = sha_short
        self.parent = []
        self.author = None
        self.committer = None
        self.message = []
        self.message_oneline = None
        self.gpgsig = []
        self.x = None
        self.x2 = None
        self.y = None
        self.color = None
        self.author_date = None
        self.committer_date = None
    
    def p(self):
        return self.x, self.y

    def p2(self):
        if self.x2 is None:
            return self.p()
        return self.x2, self.y
    
    def p0(self):
        return 0, self.y

    def __repr__(self):
        return "Commit(p={}, sha={}, message={}, )".format(self.p(), self.sha, self.message_oneline)
