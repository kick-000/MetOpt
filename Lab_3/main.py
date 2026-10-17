import sympy as sp

x, y = sp.symbols("x y", real=True)
lam = sp.symbols("lambda", real=True)
f = x + y
constraints = [x**2 + y**2 - 2]
variables = [x, y]
multipliers = [lam]
TOL = 1e-8


L = f + sum(m * h for m, h in zip(multipliers, constraints))
stationarity = [sp.diff(L, v) for v in variables]
equations = stationarity + constraints
unknowns = variables + multipliers


print("Целевая функция:")
print(f"f(x, y) = {f}")

print("\nОграничения:")
for i, h in enumerate(constraints, 1):
    print(f"h{i}(x, y) = {h} = 0")

print("\nФункция Лагранжа:")
print(f"L(x, y, lambda) = {L}")

print("\nУравнения стационарности:")
for eq in stationarity:
    print(f"  {eq} = 0")

print("\nПолная система Лагранжа:")
for eq in equations:
    print(f"  {eq} = 0")


solutions = sp.solve(equations, unknowns, dict=True)
candidates = []

for sol in solutions:
    if not all(v in sol for v in unknowns):
        print("неполное решение")
        print(sol)
        continue

    point = {v: sp.simplify(sol[v]) for v in variables}
    mult = {m: sp.simplify(sol[m]) for m in multipliers}


    real_solution = True

    for v in unknowns:
        value = sp.simplify(sol[v])

        if value.is_real is False:
            real_solution = False
            break

        if value.is_real is None:
            if abs(complex(sp.N(value)).imag) > TOL:
                real_solution = False
                break

    if not real_solution:
        continue


    residuals = [sp.simplify(h.subs(point)) for h in constraints]
    feasible = all(abs(float(sp.N(r))) <= TOL for r in residuals)
    candidates.append({"point": point,"multipliers": mult,"value": sp.simplify(f.subs(point)),"residuals": residuals,"feasible": feasible})


for i, c in enumerate(candidates, 1):
    print(f"\nКандидат {i}:")
    print("точка:", tuple(c["point"][v] for v in variables))
    print("множители:", tuple(c["multipliers"][m] for m in multipliers))
    print("значение функции:", c["value"])
    print("невязки ограничений:", c["residuals"])
    print("допустимость:", "да" if c["feasible"] else "нет")



feasible = [c for c in candidates if c["feasible"]]
print()
if not feasible:
    print("глобальный минимум: не определён")
    print("глобальный максимум: не определён")
    print("основание классификации: допустимые кандидаты не найдены")
else:
    minimum = min(feasible, key=lambda c: float(sp.N(c["value"])))
    maximum = max(feasible, key=lambda c: float(sp.N(c["value"])))

    min_point = tuple(minimum["point"][v] for v in variables)
    max_point = tuple(maximum["point"][v] for v in variables)

    print(f"глобальный минимум: f = {minimum['value']}, точка {min_point}")
    print(f"глобальный максимум: f = {maximum['value']}, точка {max_point}")
