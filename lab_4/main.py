from functools import lru_cache
from itertools import product
from math import floor, ceil
from time import perf_counter
import csv


ASSET_NAMES = ("ЦБ1", "ЦБ2", "Депозит")
INITIAL_ASSETS = (100.0, 800.0, 400.0)
INITIAL_CASH = 600.0

PACKAGE = (25.0, 200.0, 100.0)
FEE = (1.0, 14.0, 5.0)
MINIMUM = (30.0, 150.0, 100.0)

SCENARIO_NAMES = ("Благоприятная", "Нейтральная", "Негативная")

PROB = (
    (0.60, 0.30, 0.10),
    (0.30, 0.20, 0.50),
    (0.40, 0.40, 0.20),
)

STAGE = (
    (
        (1.20, 1.10, 1.07),
        (1.05, 1.02, 1.03),
        (0.80, 0.95, 1.00),
    ),
    (
        (1.40, 1.15, 1.01),
        (1.05, 1.00, 1.00),
        (0.60, 0.90, 1.00),
    ),
    (
        (1.15, 1.12, 1.05),
        (1.05, 1.01, 1.01),
        (0.70, 0.94, 1.00),
    ),
)

N_STAGES = 3
N_SCENARIOS = 3
EPS = 1e-9
ROUND_DIGITS = 10


def normalize_state(assets, cash):
    return ( tuple(round(float(x), ROUND_DIGITS) for x in assets),round(float(cash), ROUND_DIGITS),)



def apply_action(assets, cash, action):

    new_assets = tuple(
        assets[i] + PACKAGE[i] * action[i]
        for i in range(3)
    )

    new_cash = float(cash)
    for i, count in enumerate(action):
        if count > 0:
            new_cash -= count * (PACKAGE[i] + FEE[i])
        elif count < 0:
            new_cash += (-count) * (PACKAGE[i] - FEE[i])

    return new_assets, new_cash


def apply_market(assets, scenario, stage):
    return tuple(
        assets[i] * STAGE[stage][scenario][i]
        for i in range(3)
    )


def check_state(assets, cash):
    return (
        all(assets[i] >= MINIMUM[i] - 1e-7 for i in range(3))
        and cash >= -1e-7
    )


def generate_actions(assets, cash):

    sell_limits = []
    for i in range(3):
        available = assets[i] - MINIMUM[i]
        max_sell = max( 0, floor((available + EPS) / PACKAGE[i]))
        sell_limits.append(max_sell)

    for sells in product(
        *(range(limit + 1) for limit in sell_limits)
    ):
        assets_after_sales = tuple(
            assets[i] - sells[i] * PACKAGE[i]
            for i in range(3)
        )
        cash_after_sales = cash + sum(
            sells[i] * (PACKAGE[i] - FEE[i])
            for i in range(3)
        )

        buys = [0, 0, 0]

        def generate_buys(i, remaining_cash):
            if i == 3:
                action = tuple(buys[j] - sells[j] for j in range(3))
                final_assets = tuple(
                    assets_after_sales[j] + buys[j] * PACKAGE[j]
                    for j in range(3)
                )
                yield action, final_assets, remaining_cash
                return

            if sells[i] > 0:
                yield from generate_buys(i + 1, remaining_cash)
                return

            deficit = MINIMUM[i] - assets_after_sales[i]
            min_buy = max( 0,ceil((deficit - EPS) / PACKAGE[i]))
            unit_cost = PACKAGE[i] + FEE[i]
            max_buy = floor((remaining_cash + EPS) / unit_cost)

            if min_buy > max_buy:
                return

            for count in range(min_buy, max_buy + 1):
                cost = count * unit_cost
                if cost <= remaining_cash + EPS:
                    buys[i] = count
                    yield from generate_buys(i + 1, remaining_cash - cost)

            buys[i] = 0

        yield from generate_buys(0, cash_after_sales)


def generate_stage2_actions(assets, cash):
    required_buys = []
    sell_limits = []
    for i in range(3):
        deficit = MINIMUM[i] - assets[i]
        required = max(0, ceil((deficit - EPS) / PACKAGE[i]))
        required_buys.append(required)
        if required:
            sell_limits.append(0)
        else:
            sell_limits.append(
                max(0, floor((assets[i] - MINIMUM[i] + EPS) / PACKAGE[i])))

    required_buys = tuple(required_buys)
    required_cost = sum(
        required_buys[i] * (PACKAGE[i] + FEE[i])
        for i in range(3)
    )

    if cash + EPS >= required_cost:
        sell_ranges = ( range(sell_limits[0] + 1), range(1), range(1),)
    else:
        sell_ranges = tuple(range(limit + 1) for limit in sell_limits)

    for sells in product(*sell_ranges):
        cash_after_sales = cash + sum(
            sells[i] * (PACKAGE[i] - FEE[i])
            for i in range(3)
        )
        if cash_after_sales + EPS < required_cost:
            continue

        buys = required_buys
        action = tuple(buys[i] - sells[i] for i in range(3))
        assets_after = tuple(
            assets[i] - sells[i] * PACKAGE[i] + buys[i] * PACKAGE[i]
            for i in range(3)
        )
        cash_after = cash_after_sales - required_cost

        if check_state(assets_after, cash_after):
            yield action, assets_after, cash_after



def terminal_action(assets, cash):
    expected_factors = tuple(
        sum(PROB[2][j] * STAGE[2][j][i] for j in range(N_SCENARIOS))
        for i in range(3)
    )

    required_buys = []
    sell_limits = []
    for i in range(3):
        deficit = MINIMUM[i] - assets[i]
        required_buys.append(max(0, ceil((deficit - EPS) / PACKAGE[i])))

        if required_buys[i] > 0:
            sell_limits.append(0)
        else:
            sell_limits.append( max(0, floor((assets[i] - MINIMUM[i] + EPS) / PACKAGE[i] )))

    required_buys = tuple(required_buys)
    required_cost = sum(
        required_buys[i] * (PACKAGE[i] + FEE[i])
        for i in range(3)
    )

    if cash + EPS >= required_cost:
        best_action = required_buys
        assets_after, cash_after = apply_action(assets, cash, best_action)
        best_value = sum(
            assets_after[i] * expected_factors[i]
            for i in range(3)
        ) + cash_after
    else:
        best_value = float("-inf")
        best_action = None

        for sells in product(
            *(range(limit + 1) for limit in sell_limits)
        ):
            buys = required_buys

            assets_after = tuple(
                assets[i] - sells[i] * PACKAGE[i] + buys[i] * PACKAGE[i]
                for i in range(3)
            )

            cash_after = cash
            for i in range(3):
                cash_after += sells[i] * (PACKAGE[i] - FEE[i])
                cash_after -= buys[i] * (PACKAGE[i] + FEE[i])

            if cash_after < -EPS:
                continue

            action = tuple(buys[i] - sells[i] for i in range(3))
            value = sum(
                assets_after[i] * expected_factors[i]
                for i in range(3)
            ) + cash_after

            if value > best_value + EPS:
                best_value = value
                best_action = action

    if best_action is None:
        return None

    assets_after, cash_after = apply_action(assets, cash, best_action)
    return best_action, assets_after, cash_after, best_value




@lru_cache(maxsize=None)
def bellman(stage, assets, cash):
    assets = tuple(assets)
    cash = float(cash)
    if stage == N_STAGES - 1:
        terminal = terminal_action(assets, cash)
        if terminal is None:
            raise RuntimeError("На последнем этапе нет допустимого управления.")

        action, assets_after, cash_after, expected_final = terminal
        return expected_final, action

    best_value = float("-inf")
    best_action = None

    action_generator = (
        generate_actions(assets, cash)
        if stage == 0
        else generate_stage2_actions(assets, cash))

    for action, assets_after, cash_after in action_generator:
        expected_value = 0.0

        for scenario in range(N_SCENARIOS):
            next_assets = apply_market(assets_after, scenario, stage)
            next_assets, next_cash = normalize_state(next_assets, cash_after)

            next_value, _ = bellman( stage + 1,next_assets,next_cash)
            expected_value += PROB[stage][scenario] * next_value

        if expected_value > best_value + EPS:
            best_value = expected_value
            best_action = action

    if best_action is None:
        raise RuntimeError(f"Не найдено допустимое управление на этапе {stage + 1}.")

    return best_value, best_action



def audit_stage2_on_optimal_path(first_action):
    assets_after_first, cash_after_first = apply_action( INITIAL_ASSETS, INITIAL_CASH, first_action)
    results = []

    for scenario1 in range(N_SCENARIOS):
        assets2 = apply_market(assets_after_first, scenario1, 0)
        assets2, cash2 = normalize_state(assets2, cash_after_first)

        full_best_value = float("-inf")
        full_best_action = None
        checked_actions = 0

        for action, assets_after_trade, cash_after_trade in generate_actions(assets2, cash2):
            checked_actions += 1
            expected_value = 0.0
            feasible = True

            for scenario2 in range(N_SCENARIOS):
                assets3 = apply_market(assets_after_trade, scenario2, 1)
                assets3, cash3 = normalize_state(assets3, cash_after_trade)
                terminal = terminal_action(assets3, cash3)
                if terminal is None:
                    feasible = False
                    break
                expected_value += PROB[1][scenario2] * terminal[3]

            if feasible and expected_value > full_best_value + EPS:
                full_best_value = expected_value
                full_best_action = action

        pruned_value, pruned_action = bellman(
            1, assets2, cash2
        )

        if abs(full_best_value - pruned_value) > 1e-6:
            raise AssertionError(
                "Отсечение второго этапа изменило результат на ветви "
                f"{SCENARIO_NAMES[scenario1]}: полный перебор="
                f"{full_best_value:.9f}, сокращенный="
                f"{pruned_value:.9f}."
            )

        results.append({
            "scenario": SCENARIO_NAMES[scenario1],
            "actions_checked": checked_actions,
            "full_value": full_best_value,
            "full_action": full_best_action,
            "pruned_value": pruned_value,
            "pruned_action": pruned_action,
        })

    return results


def action_text(action):
    operations = []
    for i, count in enumerate(action):
        if count > 0:
            operations.append(f"купить {ASSET_NAMES[i]}: {count} пак.")
        elif count < 0:
            operations.append(f"продать {ASSET_NAMES[i]}: {-count} пак.")
    return "; ".join(operations) if operations else "сделки не совершать"


def commission_for(action):
    return sum(abs(action[i]) * FEE[i] for i in range(3))


def restore_strategy():
    nodes = []
    leaves = []

    def walk(stage, history, assets, cash, probability_prefix,
             accumulated_commission, operation_history):
        assets, cash = normalize_state(assets, cash)
        value, action = bellman(stage, assets, cash)
        assets_after, cash_after = apply_action(assets, cash, action)

        if not check_state(assets_after, cash_after):
            raise AssertionError("Нарушено ограничение после сделки.")

        current_commission = commission_for(action)
        new_commission = accumulated_commission + current_commission

        new_operations = operation_history
        if action != (0, 0, 0):
            new_operations += (f"Этап {stage + 1}: {action_text(action)}",)

        nodes.append({
            "stage": stage + 1,
            "history": history,
            "assets_before": assets,
            "cash_before": cash,
            "action": action,
            "action_text": action_text(action),
            "assets_after": assets_after,
            "cash_after": cash_after,
            "commission": current_commission,
            "bellman_value": value,
        })

        for scenario in range(N_SCENARIOS):
            next_assets = apply_market(assets_after, scenario, stage)
            probability = probability_prefix * PROB[stage][scenario]
            next_history = history + (scenario,)

            if stage < N_STAGES - 1:
                walk(stage + 1,next_history,next_assets,cash_after,probability,new_commission, new_operations,
                )
            else:
                final_capital = sum(next_assets) + cash_after
                net_income = final_capital - (sum(INITIAL_ASSETS) + INITIAL_CASH)
                leaves.append({
                    "history": next_history,
                    "probability": probability,
                    "operations": " | ".join(new_operations) or "нет",
                    "commission": new_commission,
                    "final_assets": next_assets,
                    "final_cash": cash_after,
                    "final_capital": final_capital,
                    "net_income": net_income,
                    "return_pct": net_income / (
                        sum(INITIAL_ASSETS) + INITIAL_CASH) * 100.0,
                })

    walk(0, (), INITIAL_ASSETS, INITIAL_CASH,1.0, 0.0, ())
    return nodes, leaves


def run_tests(nodes, leaves, bellman_value):
    assert len(nodes) == 13, f"Ожидалось 13 узлов, получено {len(nodes)}."
    assert len(leaves) == 27, f"Ожидалось 27 исходов, получено {len(leaves)}."

    probability_sum = sum(x["probability"] for x in leaves)
    assert abs(probability_sum - 1.0) < 1e-8

    for node in nodes:
        assert check_state(node["assets_after"], node["cash_after"])
        assert all(isinstance(x, int) for x in node["action"])

    expected_by_tree = sum(
        x["probability"] * x["final_capital"]
        for x in leaves
    )
    assert abs(expected_by_tree - bellman_value) < 1e-5

    return probability_sum, expected_by_tree


def save_tree_csv(leaves):
    filename = "tree_outcomes_bellman.csv"
    with open(filename, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow([
            "№", "Сценарии", "Вероятность", "Операции",
            "Комиссии, д.е.", "Конечный капитал, д.е.",
            "Чистый доход, д.е.", "Доходность, %"
        ])

        for number, leaf in enumerate(leaves, 1):
            history = " → ".join(SCENARIO_NAMES[x] for x in leaf["history"])
            writer.writerow([
                number,
                history,
                f'{leaf["probability"]:.6f}',
                leaf["operations"],
                f'{leaf["commission"]:.2f}',
                f'{leaf["final_capital"]:.6f}',
                f'{leaf["net_income"]:.6f}',
                f'{leaf["return_pct"]:.6f}',
            ])
    return filename


def main():
    start = perf_counter()

    initial_capital = sum(INITIAL_ASSETS) + INITIAL_CASH
    for probabilities in PROB:
        assert abs(sum(probabilities) - 1.0) < 1e-10

    initial_assets, initial_cash = normalize_state(INITIAL_ASSETS, INITIAL_CASH)
    expected_capital, first_action = bellman(0, initial_assets, initial_cash)

    audit_results = audit_stage2_on_optimal_path(first_action)

    nodes, leaves = restore_strategy()
    elapsed = perf_counter() - start

    probability_sum, expected_by_tree = run_tests(nodes, leaves, expected_capital)

    expected_income = expected_capital - initial_capital
    expected_return = expected_income / initial_capital * 100.0
    loss_probability = sum(
        x["probability"] for x in leaves
        if x["net_income"] < -EPS)
    min_income = min(x["net_income"] for x in leaves)
    max_income = max(x["net_income"] for x in leaves)

    print(f"Начальный капитал: {initial_capital:.6f} д.е.")
    print(f"Первое оптимальное действие: {action_text(first_action)}")
    for item in audit_results:
        print(
            f"  После сценария '{item['scenario']}': "
            f"проверено действий полного перебора = {item['actions_checked']}; "
            f"полное и сокращенное значения = {item['full_value']:.6f}; "
            f"действия совпали = {item['full_action'] == item['pruned_action']}" )
    print("Оптимальная стратегия")

    for node in nodes:
        history = (
            "Начальное состояние"
            if not node["history"]
            else " → ".join(SCENARIO_NAMES[x] for x in node["history"])
        )
        print(f"\nЭтап {node['stage']}: {history}")
        print(
            "До сделки: активы="
            f"{tuple(round(x, 4) for x in node['assets_before'])}, "
            f"свободные средства={node['cash_before']:.2f}"
        )
        print(f"Действие: {node['action_text']}")
        print(
            "После сделки: активы="
            f"{tuple(round(x, 4) for x in node['assets_after'])}, "
            f"свободные средства={node['cash_after']:.2f}"
        )
        print(f"Комиссия: {node['commission']:.2f} д.е.")
        print(f"Значение функции Беллмана: {node['bellman_value']:.6f}")


    print("Конечные исходы")

    for number, leaf in enumerate(leaves, 1):
        history = " → ".join(
            SCENARIO_NAMES[x] for x in leaf["history"]
        )
        print(
            f"{number:02d}. {history}; "
            f"P={leaf['probability']:.4f}; "
            f"комиссии={leaf['commission']:.2f}; "
            f"капитал={leaf['final_capital']:.4f}; "
            f"доход={leaf['net_income']:.4f}; "
            f"доходность={leaf['return_pct']:.4f}%")


    print(f"Начальный капитал: {initial_capital:.6f} д.е.")
    print(f"Ожидаемый конечный капитал: {expected_capital:.6f} д.е.")
    print(f"Ожидаемый чистый доход: {expected_income:.6f} д.е.")
    print(f"Ожидаемая доходность: {expected_return:.6f} %")
    print(f"Вероятность убытка:  {loss_probability:.6f} ({loss_probability * 100:.2f} %)")
    print(f"Минимальный доход:  {min_income:.6f} д.е.")
    print(f"Максимальный доход:  {max_income:.6f} д.е.")
    print(f"Сумма вероятностей исходов:{probability_sum:.6f}")
    print(f"Проверка по дереву:{expected_by_tree:.6f} д.е.")
    print(f"Время выполнения:{elapsed:.4f} сек.")

    csv_file = save_tree_csv(leaves)
    print(f"\nТаблица дерева сохранена: {csv_file}")

    print("\nПроверка сокращения перебора на втором этапе:" )

    audit_passed = True

    for item in audit_results:
        value_matches = abs( item["full_value"] - item["pruned_value"]) < 1e-6
        action_matches = ( item["full_action"] == item["pruned_action"])

        if not value_matches:
            audit_passed = False

        print(
            f"{item['scenario']}: "
            f"полный перебор = {item['full_value']:.6f}; "
            f"сокращенный перебор = {item['pruned_value']:.6f}; "
            f"значения совпадают = {value_matches}; "
        )


if __name__ == "__main__":
    main()
