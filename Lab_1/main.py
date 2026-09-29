
# Исходная задача
# max Z = 2*x1 + 3*x2 + x3 + 4*x4
func_coeffs = [2, 3, 1, 4]

# Ограничения:
# x1 + x2 + x3 + x4 <= 10
# 2*x1 + x2 - x3 + x4 = 8
# x2 + 2*x3 + x4 >= 5
constraints = [
    ([1, 1, 1, 1], "<=", 10),
    ([2, 1, -1, 1], "=", 8),
    ([0, 1, 2, 1], ">=", 5)
]

is_max = True



# Канонизация
def canonization(constraints):
    n = len(constraints[0][0])
    A = []
    b = []
    basis = []
    artificial = []
    variable_count = n
    for coeffs, sign, rhs in constraints:
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
            raise ValueError(
                "Неизвестный знак ограничения"
            )
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
    if not maximize:
        c = [-x for x in c]

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
        c_basis = [c[basis[i]]for i in range(m) ]

        z = sum(c_basis[i] * b[i]for i in range(m) )
        reduced = []

        for j in range(n):
            value = c[j]


            for i in range(m):
                value -= c_basis[i] * A[i][j]
            reduced.append(value)

        print()
        print("Итерация", iteration)
        print("Базис:",[f"x{x + 1}" for x in basis])
        print("b =", b)
        print("Z =", z)
        print("Оценки =", reduced)

        entering = -1
        for j in range(n):
            if reduced[j] > 1e-10:
                entering = j
                break

        if entering == -1:
            break

        leaving = -1
        min_ratio = float("inf")
        for i in range(m):


            if A[i][entering] > 1e-10:
                ratio = b[i] / A[i][entering]

                if ratio >= 0 and ratio < min_ratio:
                    min_ratio = ratio
                    leaving = i

        if leaving == -1:
            raise ValueError("Целевая функция не ограничена")

        print("Входит:", f"x{entering + 1}")
        print("Выходит:",f"x{basis[leaving] + 1}")
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

    c_basis = [ c[basis[i]] for i in range(m) ]

    z = sum(c_basis[i] * b[i] for i in range(m) )
    if not maximize:
        z = -z



    return z, x, basis


def remove_artificial(A, b, basis, artificial):
    m = len(A)
    n = len(A[0])
    artificial = set(artificial)

    for i in range(m):
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
                    continue
                raise ValueError("Не удалось удалить искусственную переменную")


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


def two_phase_simplex():

    A, b, basis, artificial, variable_count = \
        canonization(constraints)

    print()
    print("канонический вид")

    for i in range(len(A)):
        print([f"{v:g}" for v in A[i]], "=",f"{b[i]:g}")

    print("Начальный базис:", [f"x{x + 1}" for x in basis])
    print("Искусственные переменные:",[f"x{x + 1}" for x in artificial])
    print("вспомогательная задача")


    # W = x6 + x8
    # максимизируем -W
    c_phase1 = [0.0] * variable_count
    for j in artificial:
        c_phase1[j] = -1

    z1, x1, basis1 = simplex(
        c_phase1,
        A,
        b,
        basis,
        maximize=True
    )

    W_min = -z1
    print()
    print("W_min =", W_min)
    if W_min > 1e-10:
        raise ValueError("Исходная задача не имеет допустимого решения")

    print("W_min = 0 -> допустимое решение существует")


    A, b, basis, normal = remove_artificial( A, b, basis1, artificial )
    c_phase2 = []
    for i in normal:
        if i < len(func_coeffs):
            c_phase2.append(func_coeffs[i])
        else:
            c_phase2.append(0.0)
    print("Переменные:", [f"x{i + 1}" for i in normal])
    print("Коэффициенты:", c_phase2)

    print()
    print("Основная задача")
    z, x, basis = simplex( c_phase2, A, b, basis, maximize=is_max )
    full_x = [0.0] * variable_count
    for new_index, old_index in enumerate(normal):
        full_x[old_index] = x[new_index]
    return z, full_x




z, ans = two_phase_simplex()
print()
print("ответ")

print("Оптимальная точка:")
for i in range(len(func_coeffs)):
    value = ans[i]
    if abs(value) < 1e-10:
        value = 0

    print(f"x{i + 1} = {value:g}")

print()
print(f"Zmax = {z:g}")
