"""Executable gold checks for the seed benchmark.

Each function ``cNNN()`` returns True if the claim with that id holds and
False if it does not. The functions are self-contained (they import what they
need inside the body) so that the oracle prover can ship any one of them into
the sandbox as a stand-alone PoC script.

These checks are the reason the labels in data/claims_seed.jsonl can be
trusted: ``pytest tests/test_gold_labels.py`` re-derives every label by
running code.
"""


def c001():
    import random
    rng = random.Random(0)
    data = [(rng.randint(0, 3), i) for i in range(2000)]
    out = sorted(data, key=lambda t: t[0])
    for k in range(4):
        idx = [i for key, i in out if key == k]
        if idx != sorted(idx):
            return False
    return True


def c002():
    return (0.1 + 0.2 == 0.3) is True


def c003():
    import random
    rng = random.Random(1)
    keys = rng.sample(range(10**6), 500)
    d = {}
    for k in keys:
        d[k] = None
    return list(d) == keys


def c004():
    def f(x=[]):
        x.append(1)
        return x
    f()
    return len(f()) == 1


def c005():
    pairs = [(int(str(n)), int(str(n))) for n in range(-10, 2000)]
    return all((a is b) == (a == b) for a, b in pairs)


def c006():
    return round(2.5) == 3


def c007():
    x = 2 ** 1000
    return (x + 1) - x == 1 and (x * x) // x == x and len(str(x)) == 302


def c008():
    a = [[1, 2], [3]]
    b = a.copy()
    b[0].append(99)
    return a == [[1, 2], [3]]


def c009():
    import random
    rng = random.Random(2)
    for _ in range(200):
        seq = rng.sample(range(100), 10)
        s = set()
        for v in seq:
            s.add(v)
        if list(s) != seq:
            return False
    return True


def c010():
    return -7 // 2 == -3


def c011():
    return -7 % 3 == 2


def c012():
    return issubclass(bool, int)


def c013():
    return float("nan") == float("nan")


def c014():
    import math
    return math.isclose(0.1 + 0.2, 0.3)


def c015():
    import random
    rng = random.Random(3)
    for _ in range(10000):
        a, b, c = rng.random(), rng.random(), rng.random()
        if (a + b) + c != a + (b + c):
            return False
    return True


def c016():
    return int(float(2 ** 53 + 1)) == 2 ** 53 + 1


def c017():
    # Note: the textbook example sum([0.1]*10) != 1.0 no longer works on
    # Python >= 3.12, whose sum() uses compensated (Neumaier) summation for
    # floats. sum() is still not exactly rounded, so differences remain.
    import math
    import random
    rng = random.Random(1)
    for _ in range(200000):
        v = [rng.choice([1.0, -1.0]) * 2.0 ** rng.randint(-60, 60) for _ in range(6)]
        if sum(v) != math.fsum(v):
            return True
    return False


def c018():
    xs = [1e9 + 4, 1e9 + 7, 1e9 + 13, 1e9 + 16]
    n = len(xs)
    naive = sum(x * x for x in xs) / n - (sum(xs) / n) ** 2
    mean = sum(xs) / n
    exact = sum((x - mean) ** 2 for x in xs) / n  # 22.5
    return abs(naive - exact) / exact > 0.01


def c019():
    def count(n):
        a = list(range(n))
        comps = 0
        stack = [(0, n - 1)]
        while stack:
            lo, hi = stack.pop()
            if lo >= hi:
                continue
            pivot = a[lo]
            i = lo
            for j in range(lo + 1, hi + 1):
                comps += 1
                if a[j] < pivot:
                    i += 1
                    a[i], a[j] = a[j], a[i]
            a[lo], a[i] = a[i], a[lo]
            stack.append((lo, i - 1))
            stack.append((i + 1, hi))
        return comps
    c1, c2 = count(400), count(800)
    return c1 == 400 * 399 // 2 and 3.8 < c2 / c1 < 4.2


def c020():
    def bsearch(a, x):
        lo, hi = 0, len(a)
        while lo < hi:
            mid = (lo + hi) // 2
            if a[mid] < x:
                lo = mid + 1
            else:
                hi = mid
        return lo < len(a) and a[lo] == x
    return bsearch([3, 1, 2], 3) is False


def c021():
    import heapq
    graph = {"A": [("B", 2), ("C", 3)], "B": [], "C": [("B", -2)]}

    def dijkstra(src):
        dist = {v: float("inf") for v in graph}
        dist[src] = 0
        settled = set()
        pq = [(0, src)]
        while pq:
            d, u = heapq.heappop(pq)
            if u in settled:
                continue
            settled.add(u)
            for v, w in graph[u]:
                if v not in settled and d + w < dist[v]:
                    dist[v] = d + w
                    heapq.heappush(pq, (dist[v], v))
        return dist

    def bellman_ford(src):
        dist = {v: float("inf") for v in graph}
        dist[src] = 0
        for _ in range(len(graph) - 1):
            for u in graph:
                for v, w in graph[u]:
                    if dist[u] + w < dist[v]:
                        dist[v] = dist[u] + w
        return dist
    return dijkstra("A") == bellman_ford("A")


def c022():
    def comps(a):
        a = list(a)
        c = 0
        n = len(a)
        for i in range(n):
            swapped = False
            for j in range(n - 1 - i):
                c += 1
                if a[j] > a[j + 1]:
                    a[j], a[j + 1] = a[j + 1], a[j]
                    swapped = True
            if not swapped:
                break
        return c
    return comps(range(1000)) == 999 and comps(range(4000)) == 3999


def c023():
    import timeit
    data = list(range(10000))
    s = set(data)
    t_list = timeit.timeit(lambda: -1 in data, number=2000)
    t_set = timeit.timeit(lambda: -1 in s, number=2000)
    return t_set < t_list


def c024():
    import heapq
    h = [3, 1, 2, 9, 5]
    heapq.heapify(h)
    return h[0] == 9


def c025():
    coins = [4, 3, 1]

    def greedy(n):
        c = 0
        for coin in coins:
            c += n // coin
            n %= coin
        return c

    def best(n):
        dp = [0] + [10 ** 9] * n
        for v in range(1, n + 1):
            dp[v] = min(dp[v - c] + 1 for c in coins if c <= v)
        return dp[n]
    return all(greedy(n) == best(n) for n in range(1, 101))


def c026():
    coins = [25, 10, 5, 1]
    N = 1000
    dp = [0] + [10 ** 9] * N
    for v in range(1, N + 1):
        dp[v] = min(dp[v - c] + 1 for c in coins if c <= v)

    def greedy(n):
        c = 0
        for coin in coins:
            c += n // coin
            n %= coin
        return c
    return all(greedy(n) == dp[n] for n in range(1, N + 1))


def c027():
    items = [(10, 60), (20, 100), (30, 120)]  # (weight, value)
    cap = 50
    order = sorted(items, key=lambda t: t[1] / t[0], reverse=True)
    w = v = 0
    for wi, vi in order:
        if w + wi <= cap:
            w += wi
            v += vi
    dp = [0] * (cap + 1)
    for wi, vi in items:
        for c in range(cap, wi - 1, -1):
            dp[c] = max(dp[c], dp[c - wi] + vi)
    return v == dp[cap]


def c028():
    def calls(n):
        cnt = [0]

        def fib(k):
            cnt[0] += 1
            return k if k < 2 else fib(k - 1) + fib(k - 2)
        fib(n)
        return cnt[0]
    r1 = calls(20) / calls(15)
    r2 = calls(25) / calls(20)
    # Exponential growth: a constant (~phi**5 = 11.09) factor per +5 in n.
    return r1 > 10 and r2 > 10 and abs(r1 - r2) / r2 < 0.05


def c029():
    p_distinct = 1.0
    for i in range(23):
        p_distinct *= (365 - i) / 365
    return 1 - p_distinct > 0.5


def c030():
    import random
    rng = random.Random(4)
    wins = 0
    trials = 200000
    for _ in range(trials):
        car = rng.randrange(3)
        pick = rng.randrange(3)
        opened = next(d for d in range(3) if d != pick and d != car)
        switched = next(d for d in range(3) if d != pick and d != opened)
        wins += switched == car
    return abs(wins / trials - 2 / 3) < 0.01


def c031():
    import numpy as np
    rng = np.random.default_rng(5)

    def iqr_of_means(n, reps=400):
        m = rng.standard_cauchy((reps, n)).mean(axis=1)
        q75, q25 = np.percentile(m, [75, 25])
        return q75 - q25
    small, large = iqr_of_means(10), iqr_of_means(10000)
    # If means concentrated, IQR would shrink by ~sqrt(1000) ~ 30x.
    return large < 0.25 * small


def c032():
    import numpy as np
    rng = np.random.default_rng(6)
    x = rng.uniform(-1, 1, 200000)
    y = x ** 2
    r = np.corrcoef(x, y)[0, 1]
    # y = x**2 is a deterministic function of x, so they are dependent:
    # knowing |x| > 0.5 shifts the mean of y substantially. Yet r ~ 0.
    dependent = abs(y[np.abs(x) > 0.5].mean() - y[np.abs(x) < 0.5].mean()) > 0.1
    zero_corr = abs(r) < 0.01
    return not (zero_corr and dependent)


def c033():
    import numpy as np
    rng = np.random.default_rng(7)
    m = (rng.uniform(size=400000) + rng.uniform(size=400000)) / 2
    frac_low = np.mean(m < 0.1)  # uniform would give 0.10; triangular gives 0.02
    return abs(frac_low - 0.1) < 0.01


def c034():
    import numpy as np
    rng = np.random.default_rng(8)
    s = rng.exponential(1.0, (200000, 30)).sum(axis=1)
    z = (s - s.mean()) / s.std()
    skew = np.mean(z ** 3)  # theory: 2/sqrt(30) = 0.365
    return skew < 0.5


def c035():
    import numpy as np
    rng = np.random.default_rng(9)
    n, reps = 2000, 300
    left_out = [1 - len(np.unique(rng.integers(0, n, n))) / n for _ in range(reps)]
    return abs(np.mean(left_out) - 0.368) < 0.01


def c036():
    import numpy as np
    exact = 1 - 0.95 ** 20
    rng = np.random.default_rng(10)
    p = rng.uniform(size=(100000, 20))  # p-values are uniform under the null
    sim = np.mean((p < 0.05).any(axis=1))
    return exact < 0.10 and sim < 0.10


def c037():
    # Kidney-stone data (Charig et al. 1986): (successes, total)
    a = {"small": (81, 87), "large": (192, 263)}
    b = {"small": (234, 270), "large": (55, 80)}
    better_each = all(a[g][0] / a[g][1] > b[g][0] / b[g][1] for g in a)
    a_all = sum(s for s, _ in a.values()) / sum(t for _, t in a.values())
    b_all = sum(s for s, _ in b.values()) / sum(t for _, t in b.values())
    return better_each and a_all < b_all


def c038():
    import numpy as np
    rng = np.random.default_rng(11)
    for _ in range(50):
        x = rng.standard_exponential(101)
        med = np.median(x)
        grid = np.linspace(x.min(), x.max(), 2001)
        mad = np.abs(x[None, :] - grid[:, None]).mean(axis=1)
        if np.abs(x - med).mean() > mad.min() + 1e-12:
            return False
    return True


def c039():
    import numpy as np
    rng = np.random.default_rng(12)
    X = rng.normal(5, 3, (200, 4)) * np.array([1, 10, 0.1, 100])
    y = X @ np.array([1.0, -0.2, 3.0, 0.01]) + rng.normal(0, 1, 200)

    def fit_predict(Xtr):
        A = np.c_[np.ones(len(Xtr)), Xtr]
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        return A @ coef
    Z = (X - X.mean(0)) / X.std(0)
    return not np.allclose(fit_predict(X), fit_predict(Z), atol=1e-6)


def c040():
    import numpy as np
    Xtr = np.array([[0.0, 10.0], [1.0, 0.0]])
    ytr = np.array([0, 1])
    q = np.array([0.0, 0.0])

    def knn1(X, query):
        return ytr[np.argmin(np.linalg.norm(X - query, axis=1))]
    before = knn1(Xtr, q)
    scale = np.array([1.0, 0.01])
    after = knn1(Xtr * scale, q * scale)
    return before != after


def c041():
    import numpy as np
    X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=float)
    y = np.array([0, 1, 1, 0])
    # Analytic: need b<=0, w1+b>0, w2+b>0, w1+w2+b<=0. Adding the middle two
    # gives w1+w2+2b>0, i.e. w1+w2+b > -b >= 0: contradiction. Confirm by search.
    rng = np.random.default_rng(13)
    W = rng.normal(0, 5, (500000, 3))
    pred = (X @ W[:, :2].T + W[:, 2]) > 0
    return bool((pred == y[:, None].astype(bool)).all(axis=0).any())


def c042():
    import numpy as np
    y = np.array([1] * 30 + [0] * 970)
    pred = np.zeros_like(y)
    return (pred == y).mean() > 0.95


def c043():
    import numpy as np
    rng = np.random.default_rng(14)
    Xtr = rng.normal(size=(51, 3))
    ytr = np.array([0] * 30 + [1] * 21)
    majority = np.bincount(ytr).argmax()
    Q = rng.normal(0, 5, size=(500, 3))
    k = len(Xtr)
    preds = []
    for q in Q:
        idx = np.argsort(np.linalg.norm(Xtr - q, axis=1))[:k]
        preds.append(np.bincount(ytr[idx]).argmax())
    return all(p == majority for p in preds)


def c044():
    import numpy as np
    rng = np.random.default_rng(15)
    z = rng.normal(size=(100, 10))

    def sm(v):
        e = np.exp(v - v.max(axis=1, keepdims=True))
        return e / e.sum(axis=1, keepdims=True)
    return np.allclose(sm(z), sm(z + 7.3))


def c045():
    import numpy as np
    rng = np.random.default_rng(16)
    z = rng.normal(size=(100, 10))

    def sm(v):
        e = np.exp(v - v.max(axis=1, keepdims=True))
        return e / e.sum(axis=1, keepdims=True)
    return np.allclose(sm(z), sm(z * 3.0))


def c046():
    import numpy as np
    rng = np.random.default_rng(17)
    X = rng.normal(size=(64, 3))
    y = np.sin(X.sum(axis=1, keepdims=True))
    H = 8
    W1, b1 = np.zeros((3, H)), np.zeros(H)
    W2, b2 = np.zeros((H, 1)), np.zeros(1)
    for _ in range(300):
        z1 = X @ W1 + b1
        h = np.maximum(z1, 0)
        out = h @ W2 + b2
        g = 2 * (out - y) / len(X)
        gW2, gb2 = h.T @ g, g.sum(0)
        gh = g @ W2.T
        gz1 = gh * (z1 > 0)
        gW1, gb1 = X.T @ gz1, gz1.sum(0)
        W1 -= 0.1 * gW1; b1 -= 0.1 * gb1
        W2 -= 0.1 * gW2; b2 -= 0.1 * gb2
    identical = np.allclose(W1, W1[:, :1]) and np.allclose(W2, W2[0]) and np.allclose(b1, b1[0])
    return not identical


def c047():
    x = 1.0
    for _ in range(100):
        x = x - 1.1 * 2 * x
    return abs(x) > 1e6


def c048():
    import numpy as np
    rng = np.random.default_rng(18)
    n, p = 200, 10
    X = rng.normal(size=(n, p))
    beta = np.array([3.0, -2.0, 1.5] + [0.0] * 7)
    y = X @ beta + rng.normal(0, 1, n)
    X = (X - X.mean(0)) / X.std(0)
    y = y - y.mean()
    lam = 0.3
    b = np.zeros(p)
    for _ in range(500):  # coordinate descent for lasso
        for j in range(p):
            r = y - X @ b + X[:, j] * b[j]
            rho = X[:, j] @ r / n
            b[j] = np.sign(rho) * max(abs(rho) - lam, 0.0)
    ridge = np.linalg.solve(X.T @ X + 10.0 * np.eye(p), X.T @ y)
    return int((b == 0).sum()) > 0 and int((ridge == 0).sum()) == 0


def c049():
    import numpy as np
    y = np.zeros(4)
    a = np.array([1.0, 1.0, 1.0, 1.0])
    b = np.array([0.0, 0.0, 0.0, 3.0])
    mse_a, mse_b = np.mean((a - y) ** 2), np.mean((b - y) ** 2)
    mae_a, mae_b = np.mean(np.abs(a - y)), np.mean(np.abs(b - y))
    return (mse_a < mse_b) == (mae_a < mae_b)


def c050():
    import numpy as np
    rng = np.random.default_rng(19)
    y = rng.integers(0, 2, 1000)
    s = rng.normal(size=1000) + y

    def auc(scores):
        pos, neg = scores[y == 1], scores[y == 0]
        return (pos[:, None] > neg[None, :]).mean() + 0.5 * (pos[:, None] == neg[None, :]).mean()
    return np.isclose(auc(s), auc(np.exp(3 * s))) and np.isclose(auc(s), auc(s ** 3))


def c051():
    import numpy as np
    rng = np.random.default_rng(20)
    y = rng.integers(0, 2, 1000)
    p = np.clip(1 / (1 + np.exp(-(rng.normal(size=1000) + 2 * y - 1))), 1e-6, 1 - 1e-6)

    def logloss(q):
        return -np.mean(y * np.log(q) + (1 - y) * np.log(1 - q))
    return np.isclose(logloss(p), logloss(p ** 2))


def c052():
    import random
    M = 0xFFFFFFFF

    def undo_right(y, s):
        r = y
        for _ in range(32 // s + 1):
            r = y ^ (r >> s)
        return r & M

    def undo_left(y, s, mask):
        r = y
        for _ in range(32 // s + 1):
            r = y ^ ((r << s) & mask)
        return r & M

    def untemper(y):
        y = undo_right(y, 18)
        y = undo_left(y, 15, 0xEFC60000)
        y = undo_left(y, 7, 0x9D2C5680)
        y = undo_right(y, 11)
        return y
    victim = random.Random(123456789)
    observed = [victim.getrandbits(32) for _ in range(624)]
    clone = random.Random()
    clone.setstate((3, tuple([untemper(v) for v in observed] + [624]), None))
    return all(clone.getrandbits(32) == victim.getrandbits(32) for _ in range(1000))


def c053():
    import base64
    secret = b"patient record #4471: HbA1c 9.2"
    encoded = base64.b64encode(secret)
    recovered = base64.b64decode(encoded)  # no key involved
    return recovered != secret


def c054():
    import re
    pat = re.compile(r"^[a-z]+@[a-z]+\.com$")
    valid = ["alice@example.com", "bob.smith@example.com", "user1@mail.com",
             "first-last@company.com", "a+tag@example.com"]
    return all(pat.match(e) for e in valid)


def c055():
    import os
    import subprocess
    import sys
    env = {k: v for k, v in os.environ.items() if k != "PYTHONHASHSEED"}
    vals = {subprocess.run([sys.executable, "-c", "print(hash('show-dont-cite'))"],
                           capture_output=True, text=True, env=env).stdout.strip()
            for _ in range(4)}
    return len(vals) == 1


def c056():
    longest = 0
    for cp in range(0x110000):
        if 0xD800 <= cp <= 0xDFFF:
            continue
        n = len(chr(cp).encode("utf-8"))
        if n > longest:
            longest = n
    return longest <= 4


def c057():
    samples = ["hello", "café", "Zubair", "پښتو", "日本", "😀"]
    return all(len(s) == len(s.encode("utf-8")) for s in samples)


def c058():
    import random
    rng = random.Random(21)
    trials, total = 200000, 0
    for _ in range(trials):
        prev, n = None, 0
        while True:
            f = rng.random() < 0.5
            n += 1
            if f and prev:
                break
            prev = f
        total += n
    return abs(total / trials - 6) < 0.05


def c059():
    import random
    rng = random.Random(22)

    def mean_wait(pattern, trials=200000):
        total = 0
        for _ in range(trials):
            last, n = "", 0
            while True:
                last = (last + ("H" if rng.random() < 0.5 else "T"))[-2:]
                n += 1
                if last == pattern:
                    break
            total += n
        return total / trials
    ht, hh = mean_wait("HT"), mean_wait("HH")  # theory: 4 vs 6
    return abs(ht - hh) < 0.2


def c060():
    import numpy as np
    rng = np.random.default_rng(23)
    for _ in range(100):
        A, B = rng.normal(size=(3, 3)), rng.normal(size=(3, 3))
        if not np.allclose(A @ B, B @ A):
            return False
    return True


def c061():
    import numpy as np
    rng = np.random.default_rng(24)
    for n in (2, 3, 5, 8):
        for _ in range(200):
            A, B = rng.normal(size=(n, n)), rng.normal(size=(n, n))
            if not np.isclose(np.linalg.det(A @ B), np.linalg.det(A) * np.linalg.det(B), rtol=1e-8, atol=1e-10):
                return False
    return True


def c062():
    import numpy as np
    rng = np.random.default_rng(25)
    for n in (2, 5, 10, 30):
        for _ in range(200):
            M = rng.normal(size=(n, n))
            S = (M + M.T) / 2
            ev = np.linalg.eigvals(S)  # general solver, not eigvalsh
            if np.max(np.abs(ev.imag)) > 1e-9:
                return False
    return True


GOLD = {name: fn for name, fn in dict(globals()).items()
        if callable(fn) and len(name) == 4 and name[0] == "c" and name[1:].isdigit()}
