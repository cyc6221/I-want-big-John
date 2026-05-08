import math


def pad2(value: int) -> str:
    return f"{value:02d}"


def key_of(numbers: list[int]) -> str:
    return ",".join(pad2(n) for n in numbers)


def draw_key_of(numbers: list[int], second_zone: int) -> str:
    return f"{key_of(numbers)}|{pad2(second_zone)}"


def mean(values: list[float]) -> float:
    return sum(values) / (len(values) or 1)


def std(values: list[float], avg: float) -> float:
    variance = sum((value - avg) ** 2 for value in values) / (len(values) or 1)
    return math.sqrt(variance) or 1.0


def z_score(value: float, avg: float, deviation: float) -> float:
    return (value - avg) / (deviation or 1.0)


def circular_run_max(numbers: list[int], min_number: int = 1, max_number: int = 38) -> int:
    values = set(numbers)
    best = 0

    for number in values:
        prev_number = max_number if number == min_number else number - 1
        if prev_number in values:
            continue

        length = 1
        current = number
        while True:
            next_number = min_number if current == max_number else current + 1
            if next_number not in values:
                break
            current = next_number
            length += 1
            if length >= len(values):
                break

        best = max(best, length)

    return best


def number_features(numbers: list[int]) -> dict:
    odd_count = sum(1 for n in numbers if n % 2 == 1)
    low_count = sum(1 for n in numbers if n <= 19)
    spread = max(numbers) - min(numbers)
    decade_count = len({(n - 1) // 10 for n in numbers})
    return {
        "odd_count": odd_count,
        "even_count": len(numbers) - odd_count,
        "low_count": low_count,
        "high_count": len(numbers) - low_count,
        "sum": sum(numbers),
        "spread": spread,
        "decade_count": decade_count,
        "max_run": circular_run_max(numbers),
    }
