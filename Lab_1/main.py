
def expand_free_variables(func_coeffs, constraints, free_indices):
    n = len(func_coeffs)
    new_coeffs = []
    mapping = []
    new_constraints = []

    for i in range(n):
        if i in free_indices:
            plus_index = len(new_coeffs)
            new_coeffs.extend([func_coeffs[i], -func_coeffs[i]])
            minus_index = plus_index + 1
            mapping.append((plus_index, minus_index))
        else:
            index = len(new_coeffs)
            new_coeffs.append(func_coeffs[i])
            mapping.append((index,))
    for coeffs, sign, rhs in constraints:
        new_row = []
        for i, coefficient in enumerate(coeffs):
            if i in free_indices:
                new_row.extend([coefficient, -coefficient])
            else:
                new_row.append(coefficient)

        new_constraints.append((new_row, sign, rhs))

    return new_coeffs, new_constraints, mapping


def restore_original_variables(expanded_x, mapping):
    result = []
    for indices in mapping:
        if len(indices) == 2:
            value = expanded_x[indices[0]] - expanded_x[indices[1]]
        else:
            value = expanded_x[indices[0]]
        if abs(value) < 1e-10:
            value = 0.0
        result.append(value)

    return result

# Канонизация
def canonization(constraints):
    n = len(constraints[0][0])
    A = []
    b = []
    basis = []
    artificial = []
    variable_count = n
    for coeffs, sign, rhs in constraints:
        if rhs < 0:
            coeffs = [-x for x in coeffs]
            rhs = -rhs

            if sign == "<=":
                sign = ">="
            elif sign == ">=":
                sign = "<="

        row = coeffs.copy()
        while len(row) < variable_count:
            row.append(0)
        if sign == "<=":
            for old_row in A:
                old_row.append(0)
            row.append(1)
            basis.append(variable_count)
            variable_count += 1
        elif sign == ">=":
            for old_row in A:
                old_row.append(0)
            row.append(-1)
            variable_count += 1
            for old_row in A:
                old_row.append(0)
            row.append(1)
            artificial.append(variable_count)
            basis.append(variable_count)
            variable_count += 1
        elif sign == "=":
            for old_row in A:
                old_row.append(0)

            row.append(1)
            artificial.append(variable_count)
            basis.append(variable_count)
            variable_count += 1
        else:
            raise ValueError("Неизвестный знак ограничения")
        A.append(row)
        b.append(rhs)

    for row in A:
        while len(row) < variable_count:
            row.append(0)

    return A, b, basis, artificial, variable_count



# Симплекс-метод
def simplex(c, A, b, basis, maximize=True):
    A = [row[:] for row in A]
    b = b[:]
    basis = basis[:]

    m = len(A)
    n = len(A[0])

    for i in range(m):
        pivot_col = basis[i]
        pivot = A[i][pivot_col]

        if abs(pivot) < 1e-10:
            raise ValueError("Некорректный базис")

        for j in range(n):
            A[i][j] /= pivot
        b[i] /= pivot

        for k in range(m):
            if k == i:
                continue

            factor = A[k][pivot_col]
            for j in range(n):
                A[k][j] -= factor * A[i][j]
            b[k] -= factor * b[i]
    iteration = 0

    while True:
        iteration += 1
        if iteration > 10000:
            raise ValueError("Превышено максимальное число итераций")
        c_basis = [c[basis[i]] for i in range(m)]
        z = sum(c_basis[i] * b[i] for i in range(m))

        reduced = []
        for j in range(n):
            value = c[j]
            for i in range(m):
                value -= c_basis[i] * A[i][j]
            reduced.append(value)

        print()
        print("Итерация", iteration)
        print("Базис:", [f"x{x + 1}" for x in basis])
        print("b =", b)
        print("Z =", z)
        print("Оценки =", reduced)
        if maximize:
            candidates = [j for j in range(n)
                if reduced[j] > 1e-10
            ]
            entering = (max(candidates, key=lambda j: reduced[j])
                if candidates else -1
            )
        else:
            candidates = [j for j in range(n) if reduced[j] < -1e-10]
            entering = (min(candidates, key=lambda j: reduced[j]) if candidates else -1)

        if entering == -1:
            break

        leaving = -1
        min_ratio = float("inf")

        for i in range(m):
            if A[i][entering] > 1e-10:
                ratio = b[i] / A[i][entering]

                if ratio >= -1e-10 and ratio < min_ratio:
                    min_ratio = max(0.0, ratio)
                    leaving = i

        if leaving == -1:
            raise ValueError("Целевая функция не ограничена")

        print("Входит:", f"x{entering + 1}")
        print("Выходит:", f"x{basis[leaving] + 1}")
        print("Разрешающий элемент:", A[leaving][entering])
        pivot = A[leaving][entering]

        for j in range(n):
            A[leaving][j] /= pivot
        b[leaving] /= pivot

        for i in range(m):
            if i == leaving:
                continue

            factor = A[i][entering]

            for j in range(n):
                A[i][j] -= factor * A[leaving][j]
            b[i] -= factor * b[leaving]

        basis[leaving] = entering


    x = [0.0] * n
    for i in range(m):
        x[basis[i]] = b[i]
    z = sum(c[basis[i]] * b[i] for i in range(m))

    return z, x, basis, A, b



def remove_artificial(A, b, basis, artificial):
    m = len(A)
    n = len(A[0])
    artificial = set(artificial)
    i = 0
    while i < m:
        if basis[i] in artificial:
            found = False
            for j in range(n):

                # Искусственные переменные скип
                if j in artificial:
                    continue

                if abs(A[i][j]) > 1e-10:

                    pivot = A[i][j]
                    for k in range(n):
                        A[i][k] /= pivot
                    b[i] /= pivot


                    for k in range(m):
                        if k == i:
                            continue
                        factor = A[k][j]
                        for l in range(n):
                            A[k][l] -= factor * A[i][l]
                        b[k] -= factor * b[i]

                    basis[i] = j
                    found = True
                    break

            if not found:
                if abs(b[i]) < 1e-10:
                    del A[i]
                    del b[i]
                    del basis[i]
                    m -= 1
                    continue
                raise ValueError("Не удалось удалить искусственную переменную")

        i+=1

    normal = [ j for j in range(n)
               if j not in artificial ]


    new_A = []
    for i in A:
        new_A.append([i[j]
            for j in normal])

    index_map = { old: new
        for new, old in enumerate(normal)}

    new_basis = []
    for i in basis:
        if i in index_map:
            new_basis.append(index_map[i] )

    return new_A, b, new_basis, normal


def two_phase_simplex(func_coeffs, constraints, is_max=True):

    A, b, basis, artificial, variable_count = \
        canonization(constraints)

    print()
    print("канонический вид")

    for i in range(len(A)):
        print([f"{v:g}" for v in A[i]], "=",f"{b[i]:g}")

    print("Начальный базис:", [f"x{x + 1}" for x in basis])
    print("Искусственные переменные:",[f"x{x + 1}" for x in artificial])
    print()
    print("вспомогательная задача")


    c_phase1 = [0.0] * variable_count
    for j in artificial:
        c_phase1[j] = -1

    z1, x1, basis1, A1,b1= simplex(c_phase1,A, b,basis, maximize=True )

    W_min = -z1
    print()
    print("W_min =", W_min)
    if W_min > 1e-10:
        raise ValueError("Исходная задача не имеет допустимого решения")

    print("W_min = 0 -> допустимое решение существует")

    A, b = A1, b1
    basis = basis1

    A, b, basis, normal = remove_artificial( A, b, basis1, artificial )
    c_phase2 = []

    for i in normal:
        if i < len(func_coeffs):
            coefficient = func_coeffs[i]
        else:
            coefficient = 0.0
        if is_max:
            coefficient = -coefficient

        c_phase2.append(coefficient)
    print("Переменные:", [f"x{i + 1}" for i in normal])
    print("Коэффициенты:", c_phase2)

    print()
    print("Основная задача")
    z, x, basis, A, b = simplex(c_phase2, A, b, basis, maximize=False)
    if is_max:
        z = -z

    full_x = [0.0] * len(func_coeffs)
    for new_index, old_index in enumerate(normal):
        if old_index < len(func_coeffs):
            full_x[old_index] = x[new_index]
    return z, full_x


try:
    a = int(input(
        '1 — готовый пример, 2 — своя задача: '
    ))

    if a == 1:
        func_coeffs = [2, 3, 1, 4]
        is_max = True

        constraints = [
            ([1, 1, 1, 1], "<=", 10),
            ([2, 1, -1, 1], "=", 8),
            ([0, 1, 2, 1], ">=", 5)
        ]
        free_indices = set()

    elif a == 2:
        task = input("Тип задачи (max/min): ").strip().lower()

        if task not in ("max", "min"):
            raise ValueError( "Введите max или min.")

        is_max = task == "max"

        func_coeffs = list(map(float,input("Введите коэффициенты целевой функции через пробел: ").split()))

        n = len(func_coeffs)

        free_input = input("Номера свободных переменных через пробел ").strip()
        if free_input:
            free_indices = {int(i) - 1 for i in free_input.split()}
        else:
            free_indices = set()

        if any(i < 0 or i >= n for i in free_indices):
            raise ValueError("Номер свободной переменной вне диапазона.")

        m = int(input("Количество ограничений: "))

        if m <= 0:
            raise ValueError("Количество ограничений должно быть положительным.")

        constraints = []

        for i in range(m):
            coeffs = list(map(float,input(f"Коэффициенты ограничения {i + 1}: ").split()))

            if len(coeffs) != n:
                raise ValueError("Количество коэффициентов ограничения не совпадает с числом переменных.")

            sign = input("Знак ограничения (<=, >=, =): ").strip()

            if sign not in ("<=", ">=", "="):
                raise ValueError("Допустимые знаки: <=, >=, =.")

            rhs = float(input("Правая часть: "))

            constraints.append((coeffs, sign, rhs))

    else:
        raise ValueError("1 или 2")

    original_coeffs = func_coeffs[:]
    expanded_coeffs, expanded_constraints, mapping = (expand_free_variables(func_coeffs,constraints,free_indices))

    print("Исходная целевая функция:")
    print(original_coeffs)

    print("Целевая функция после замены свободных переменных:")
    print(expanded_coeffs)

    z, expanded_x = two_phase_simplex(expanded_coeffs,expanded_constraints,is_max=is_max)
    x = restore_original_variables(expanded_x,mapping)
    z_original = sum(original_coeffs[i] * x[i]for i in range(len(original_coeffs)))

    print("\nРешение")
    print("Тип задачи:", "максимизация" if is_max else "минимизация")

    for i, value in enumerate(x):
        print(f"x{i + 1} = {value:.6f}")
    print(f"Значение целевой функции = {z_original:.6f}")

except ValueError as e:
    print("\nОшибка ", e)
except ZeroDivisionError:
    print("\nОшибка решения: деление на ноль при преобразовании симплекс-таблицы.")
