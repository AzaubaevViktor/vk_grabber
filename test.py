d = {1:2, 3:4, 5:6, 7:8}

def f(a, b):
    x = a
    y = b
    z = x + y
    print(z)
    while True:
        coef = z - a
        if coef > 0:
            yield z, coef
        elif coef >= 1:
            break

        z =

for a, b in d.items():
    print("First cycle:", a, b)
    for c, d in f(a, b):
