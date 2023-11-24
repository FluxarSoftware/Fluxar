import math
import random

def fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)
def lerp(t, a, b):
    return a + t * (b - a)
def grad(hash_, x):
    h = hash_ & 15
    grad_ = 1 + (h & 7)
    if h & 8:
        grad_ = -grad_
    return grad_ * x
def perlin(x, y):
    X = int(math.floor(x)) & 255
    Y = int(math.floor(y)) & 255

    x -= math.floor(x)
    y -= math.floor(y)

    u = fade(x)
    v = fade(y)

    p = list(range(512))
    random.shuffle(p)
    p *= 2

    A = p[X] + Y
    B = p[X + 1] + Y

    return lerp(
        v,
        lerp(
            u,
            grad(p[A], x),
            grad(p[B], x - 1)
        ),
        lerp(
            u,
            grad(p[A + 1], x - 1),
            grad(p[B + 1], x - 1)
        )
    )