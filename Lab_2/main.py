import numpy as np
import sympy as sp
import matplotlib.pyplot as plt
import time

x = sp.symbols('x')

def calculate_L(df_expr, a, b):
    ddf_expr = sp.diff(df_expr, x)
    critical_points = sp.solve(ddf_expr, x)
    candidates = [a, b]

    for point in critical_points:
        if point.is_real:
            point = float(point)
            if a <= point <= b:
                candidates.append(point)

    df = sp.lambdify(x, df_expr, "numpy")
    values = [abs(float(df(point))) for point in candidates]
    L = max(values)

    return L



fs = int(input("Готовые примеры 1, 2, 3, Свой пример - 4:  "))
match fs:
    case 1:
        function_string = "x**2"
        expression = sp.sympify(function_string)
        f = sp.lambdify(x, expression, "numpy")
        a = -2
        b = 2
        eps = 0.01
    case 2:
        function_string = "(x - 2)**2 + 1"
        expression = sp.sympify(function_string)
        f = sp.lambdify(x, expression, "numpy")
        a = -1
        b = 5
        eps = 0.01
    case 3:
        expression = x**2 + sp.sin(3*x)
        f = sp.lambdify(x, expression, "numpy")
        a = -2
        b = 2
        eps = 0.01
    case 4:
        function_string = input("f(x): ")
        expression = sp.sympify(function_string)
        f = sp.lambdify(x, expression, "numpy")

        a = float(input("a: "))
        b = float(input("b: "))
        eps = float(input("eps: "))
    case _:
        print("такого пункта меню нет")
        exit()

df_expr = sp.diff(expression, x)
L = calculate_L(df_expr, a, b)
print("L =", L)

points = [(a, f(a)),(b, f(b)) ]
iterations = 0
start_time = time.time()

while True:
    iterations += 1
    points.sort()

    best_z = None
    best_G = float('inf')

    for i in range(len(points) - 1):
        xi, fi = points[i]
        xj, fj = points[i + 1]

        z = (xi + xj) / 2 - (fj - fi) / (2 * L)
        G = (fi + fj) / 2 - L * (xj - xi) / 2

        if G < best_G:
            best_G = G
            best_z = z

    new_x = best_z
    new_f = f(new_x)

    points.append((new_x, new_f))
    current_best_f = min(p[1] for p in points)

    if current_best_f - best_G  < eps:
        break

    if iterations == 10000:
        break


global_best_G = float('inf')
points.sort()

for i in range(len(points) - 1):
    xi, fi = points[i]
    xj, fj = points[i + 1]
    G = (fi + fj) / 2 - L * (xj - xi) / 2

    if G < global_best_G:
        global_best_G = G


end_time = time.time()
elapsed_time = end_time - start_time

best_point = min(points, key=lambda p: p[1])
best_x = best_point[0]
best_value = best_point[1]

print("Итераций:", iterations)
print("x* =", best_x)
print("f(x*) =", best_value)
print("Нижняя оценка =", global_best_G)
print("Погрешность =", best_value - global_best_G)
print("Время выполнения:", elapsed_time, "сек.")


X_plot = np.linspace(a, b, 1000)
Y_plot = f(X_plot)
G_values = []

for xx in X_plot:
    values = []
    for xi, fi in points:
        values.append(fi - L * abs(xx - xi))

    G_values.append(max(values))

plt.figure(figsize=(10, 6))

# Исходная функция
plt.plot(X_plot, Y_plot,color='red', label='f(x)')
plt.plot(X_plot, G_values, label='Ломаная G(x)')
# Точки
points_x = [p[0] for p in points]
points_y = [p[1] for p in points]

plt.scatter(points_x, points_y, label='Точки метода')

plt.scatter(best_x,best_value,s=100,color='green',label='Найденный минимум')

plt.xlabel('x')
plt.ylabel('f(x)')
plt.title('Результат метода Пиявского')
plt.legend()
plt.grid()

plt.show()
