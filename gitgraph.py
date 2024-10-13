from Path import Path
from collections import defaultdict
import random
from Commit import Commit
import re
from gitexec import execute

def matrix(value, rows, cols):
    return [[value for x in range(cols)] for y in range(rows)]

def find_path(p1, p2, grid) -> Path:

    path = [p1]

    def test_grid(x, y):
        if x < 0:
            return False
        if y >= len(grid):
            return False
        return grid[y][x] == False
    
    def can_go(mx, my):
        x1, y1 = path[-1]
        p = (x1 + mx, y1 + my)
        if p == p2:
            return True
        if test_grid(x1 + mx, y1 + my):
            return True
        return False
    
    def go(mx, my):
        x1, y1 = path[-1]
        path.append((x1 + mx, y1 + my))

    def get_dxdy(p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        return x2 - x1, y2 - y1

    while True:
        p0 = path[-1]
        dx, dy = get_dxdy(p0, p2)
        if dx == 0 and dy == 0:
            return Path(path)
        
        if dy < 0:
            #print("failed to find path dy < 0", p1, p2)
            return

        if dx == 0:
            if can_go(0, 1):
                go(0, 1)
                continue
            elif can_go(-1, 1):
                go(-1, 1)
                continue
        elif dx < 0:
            if can_go(-1, 1):
                go(-1, 1)
                continue
            elif can_go(0, 1):
                go(0, 1)
                continue
            elif can_go(1, 1):
                go(1, 1)
                continue
        elif dx > 0:
            if can_go(1, 1):
                go(1, 1)
                continue
            elif can_go(0, 1):
                go(0, 1)
                continue
        
        #print("find_path dx dy (not imp)", dx, dy)
        break

def get_raw_log(repo) -> list[Commit]:
    lines = execute(['git','log','--pretty=raw', '--all'], cwd = repo)
    commits = []
    commit = None
    in_sig = False
    for line in lines:
        if in_sig:
            commit.gpgsig.append(line)
            if '-----END PGP SIGNATURE-----' in line:
                in_sig = False
            continue
        m = re.match('commit ([0-9a-f]+)', line)
        if m:
            commit = Commit(m.group(1))
            commits.append(commit)
            continue
        m = re.match('tree ([0-9a-f]+)', line)
        if m:
            continue
        m = re.match('parent ([0-9a-f]+)', line)
        if m:
            commit.parent.append(m.group(1))
            continue
        m = re.match('author (.*) <(.*)> ([0-9]+) ([+-][0-9]+)', line)
        if m:
            commit.author = m.group(1)
            continue
        m = re.match('committer (.*) <(.*)> ([0-9]+) ([+-][0-9]+)', line)
        if m:
            commit.committer = m.group(1)
            continue
        m = re.match('gpgsig (.*)', line)
        if m:
            commit.gpgsig.append(m.group(1))
            in_sig = True
            continue
        commit._message.append(line)
    return commits

def get_graph(repo, color_palette = None):
    lines = execute(['git', 'log', '--graph', '--oneline', '--all'], cwd = repo, octescape=False)
    y = 0
    commits = []
    for line in lines:
        m = re.match('([\\\\/|* ]+)\\s+([0-9a-f]{6,}) (.*)', line)
        if m:
            sha = m.group(2)
            message = m.group(3)
            commit = Commit(sha)
            commit._message = message
            commit.y = y
            commit.x = line.index('*') // 2
            commits.append(commit)
            y += 1

    commit_dict = {commit.sha: commit for commit in commits}

    sha_size = len(next(iter(commit_dict.keys())))

    def trimmed(sha):
        return sha[:sha_size]

    commits2 = get_raw_log(repo)
    for commit in commits2:
        sha: str = trimmed(commit.sha)
        commit_dict[sha].parent = [trimmed(sha) for sha in commit.parent]
        t = 1
        
    paths = []

    grid = matrix(False, commits[-1].y + 1, 10)

    linked = set()

    def is_linked(c1, c2):
        return (c1.sha, c2.sha) in linked
    
    def add_path(commit: Commit, parent: Commit, path: Path):
        if path is None:
            return
        paths.append(path)
        for x, y in path._points:
            grid[y][x] = True
        path._commit = commit.sha
        path._parent = parent.sha
        linked.add((commit.sha, parent.sha))

    

    for commit in commits:
        grid[commit.y][commit.x] = True

    for i in range(5):
        commit: Commit
        for commit in commits:
            for sha in commit.parent:
                parent: Commit = commit_dict[sha]
                if is_linked(commit, parent):
                    continue
                dx = parent.x - commit.x
                dy = parent.y - commit.y
                if i == 0:
                    # short (vertical and diagonal)
                    if -2 < dx < 2 and dy == 1:
                        path = find_path(commit.p(), parent.p(), grid)
                        add_path(commit, parent, path)

                elif i == 1:
                    # vertical
                    if dx == 0:
                        path = find_path(commit.p(), parent.p(), grid)
                        add_path(commit, parent, path)

                elif i == 2:
                    # almost vertical
                    if -2 < dx < 2 and dy > 1:
                        path = find_path(commit.p(), parent.p(), grid)
                        add_path(commit, parent, path)

                elif i == 3:
                    # all other
                    path = find_path(commit.p(), parent.p(), grid)
                    add_path(commit, parent, path)

                elif i == 4:
                    # give up, draw straight line
                    path = Path([commit.p(), parent.p()])
                    add_path(commit, parent, path)

    def get_text_pos(y):
        r = 0
        for x, v in enumerate(grid[y]):
            if v:
                r = x
        return r + 1

    for commit in commits:
        commit.x2 = get_text_pos(commit.y)

    children = defaultdict(list)
    for commit in commits:
        for sha in commit.parent:
            children[sha].append(commit.sha)

    if color_palette is None:
        color_palette = [
            '#335c67','#2a9d8f','#e09f3e','#9e2a2b','#540b0e'
        ]

    commit_color = defaultdict(lambda: color_palette[0])

    def different_color(colors):
        color = random.choice(color_palette)
        while color in colors:
            color = random.choice(color_palette)
        return color

    def is_fork(sha):
        return len(children[sha]) > 1

    def is_merge(commit):
        return len(commit.parent) > 1

    for commit in reversed(commits):
        # if parent is fork change color for all but first children
        if len(commit.parent) == 0:
            pass
        else:
            parent_sha = commit.parent[0]
            if is_fork(parent_sha):
                ix = children[parent_sha].index(commit.sha)
                if ix > 0:
                    commit_color[commit.sha] = different_color([commit_color[parent_sha]])
                else:
                    commit_color[commit.sha] = commit_color[parent_sha]
            else:
                commit_color[commit.sha] = commit_color[parent_sha]
        commit.color = commit_color[commit.sha]

    path: Path
    for path in paths:
        commit = commit_dict[path._commit]
        if is_merge(commit):
            path._color = commit_color[path._parent]
        else:
            path._color = commit_color[path._commit]

    return commits, paths
