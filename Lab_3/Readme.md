## Отчёт по лабораторной работе №3
#### Решение задач многомерной условной оптимизации методом множителей Лагранжа

## Цель
Освоить метод множителей Лагранжа для поиска условных экстремумов функций нескольких переменных при ограничениях-равенствах, научиться проверять условия применимости метода, находить все точки-кандидаты и обосновывать локальный или глобальный характер найденных решений.

## Вариант 1


<img width="413" height="108" alt="image" src="https://github.com/user-attachments/assets/76be671d-6614-43e0-8145-3bd11670f2cf" />

### Решение на бумаге


<img width="691" height="804" alt="image" src="https://github.com/user-attachments/assets/14944b17-4b0a-49b9-aa66-eb16bf693e54" />
<img width="705" height="541" alt="image" src="https://github.com/user-attachments/assets/b4af508d-cf58-4d4e-bd0d-037ab4777376" />



## Решение кодом 
```
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

```

## Вывод кода:

<img width="440" height="770" alt="image" src="https://github.com/user-attachments/assets/76ea4615-06e0-4349-bab1-6baa002e890c" />

## Сводная таблица: 

| Характеристика | Ручное решение | Программное решение |
|---|---|---|
| Точки-кандидаты | (1, 1), (-1, -1) | (1, 1), (-1, -1) |
| Множители Лагранжа | λ₁ = -1/2, λ₂ = 1/2 | λ₁ = -1/2, λ₂ = 1/2 |
| Значения функции | f(1, 1) = 2, f(-1, -1) = -2 | f(1, 1) = 2, f(-1, -1) = -2 |
| Минимум | f_min = -2 в точке (-1, -1) | f_min = -2 в точке (-1, -1) |
| Максимум | f_max = 2 в точке (1, 1) | f_max = 2 в точке (1, 1) |

## Вывод:
В ходе лабораторной работы был изучен метод множителей Лагранжа для решения задач многомерной условной оптимизации. Для заданной функции \(f(x,y)=x+y\) при ограничении \(x^2+y^2=2\) была составлена функция Лагранжа и решена система уравнений стационарности.
В результате найдены две точки-кандидата: \((1,1)\) и \((-1,-1)\). Для каждой точки вычислены множитель Лагранжа, значение целевой функции и невязка ограничения.

