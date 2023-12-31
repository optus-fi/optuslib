from datetime import datetime, timezone

from ..constants import USD_LIQUIDITY_ROUND_DECIMALS, USD_VOLUME_ROUND_DECIMALS
from .time import timestamp_point
from ..schemas.dashboard.charts import PairSequence, ChartPoint
from ..schemas.dashboard.db.operation import Operation


def operation_is_swap(
    operation: Operation,
) -> bool:
    if operation.operation_type:
        return operation.operation_type.name == "swap"
    else:
        return (
            operation.token_0_amount > 0
            and operation.token_1_amount < 0
            or operation.token_0_amount < 0
            and operation.token_1_amount > 0
        )


def operation_is_add(
    operation: Operation,
) -> bool:
    if operation.operation_type:
        return operation.operation_type.name == "add"
    else:
        return operation.token_0_amount >= 0 and operation.token_1_amount >= 0


def operation_is_remove(
    operation: Operation,
) -> bool:
    if operation.operation_type:
        return operation.operation_type.name == "remove"
    else:
        return operation.token_0_amount <= 0 and operation.token_1_amount <= 0


def get_start_time(
    seq: PairSequence | dict[int, int],
    default: int,
) -> int | None:
    if isinstance(seq, PairSequence):
        return min(seq.token_0.keys(), default=default)

    if isinstance(seq, dict):
        return min(seq.keys(), default=default)

    return None


def calc_liquidity_change_map(
    operations: list[Operation],
    time_interval: int,
) -> dict[int, PairSequence]:
    change_map: dict[int, PairSequence] = {}

    for operation in operations:
        if not operation.pool:
            continue

        if operation_is_add(operation) or operation_is_remove(operation):
            time_key = timestamp_point(operation.timestamp, time_interval)

            if operation.pool.id not in change_map:
                change_map[operation.pool.id] = PairSequence()

            change_map[operation.pool.id].token_0[time_key] = (
                change_map[operation.pool.id].token_0.get(time_key, 0) + operation.token_0_amount
            )

            change_map[operation.pool.id].token_1[time_key] = (
                change_map[operation.pool.id].token_1.get(time_key, 0) + operation.token_1_amount
            )

    return change_map


def calc_liquidity_sequence_map(
    operations: list[Operation],
    time_interval: int,
    now_timestamp: int,
) -> dict[int, PairSequence]:
    change_map = calc_liquidity_change_map(operations, time_interval)

    liquidity_seq_map: dict[int, PairSequence] = {}

    for pool_id, change_seq in change_map.items():
        liquidity_seq_map[pool_id] = PairSequence()

        start_time = get_start_time(change_seq, now_timestamp)

        for time_key in range(start_time, now_timestamp, time_interval):
            liquidity_seq_map[pool_id].token_0[time_key] = liquidity_seq_map[pool_id].token_0.get(
                time_key - time_interval, 0
            ) + change_seq.token_0.get(time_key, 0)

            liquidity_seq_map[pool_id].token_1[time_key] = liquidity_seq_map[pool_id].token_1.get(
                time_key - time_interval, 0
            ) + change_seq.token_1.get(time_key, 0)

    return liquidity_seq_map


def calc_volume_change_map(
    operations: list[Operation],
    time_interval: int,
) -> dict[int, PairSequence]:
    change_map: dict[int, PairSequence] = {}

    for operation in operations:
        if not operation.pool:
            continue

        if operation_is_swap(operation):
            time_key = timestamp_point(operation.timestamp, time_interval)

            if operation.pool.id not in change_map:
                change_map[operation.pool.id] = PairSequence()

            change_map[operation.pool.id].token_0[time_key] = change_map[operation.pool.id].token_0.get(
                time_key, 0
            ) + abs(operation.token_0_amount)

            change_map[operation.pool.id].token_1[time_key] = change_map[operation.pool.id].token_1.get(
                time_key, 0
            ) + abs(operation.token_1_amount)

    return change_map


def calc_volume_sequence_map(
    operations: list[Operation],
    time_interval: int,
    now_timestamp: int,
) -> dict[int, PairSequence]:
    change_map = calc_volume_change_map(operations, time_interval)

    volume_seq_map: dict[int, PairSequence] = {}

    for pool_id, change_seq in change_map.items():
        volume_seq_map[pool_id] = PairSequence()

        start_time = get_start_time(change_seq, now_timestamp)

        for time_key in range(start_time, now_timestamp, time_interval):
            volume_seq_map[pool_id].token_0[time_key] = change_seq.token_0.get(time_key, 0)

            volume_seq_map[pool_id].token_1[time_key] = change_seq.token_1.get(time_key, 0)

    return volume_seq_map


def calc_swaps_change_map(
    operations: list[Operation],
    time_interval: int,
) -> dict[int, dict[int, int]]:
    change_map: dict[int, dict[int, int]] = {}

    for operation in operations:
        if not operation.pool:
            continue

        if operation.pool.id not in change_map:
            change_map[operation.pool.id] = {}

        if operation_is_swap(operation):
            time_key = timestamp_point(operation.timestamp, time_interval)

            change_map[operation.pool.id][time_key] = change_map[operation.pool.id].get(time_key, 0) + 1

    return change_map


def calc_swaps_sequence_map(
    operations: list[Operation],
    time_interval: int,
    now_timestamp: int,
) -> dict[int, dict[int, int]]:
    change_seq_map = calc_swaps_change_map(operations, time_interval)

    swaps_seq_map: dict[int, dict[int, int]] = {}

    for pool_id, change_seq in change_seq_map.items():
        swaps_seq_map[pool_id] = {}

        start_time = get_start_time(change_seq, now_timestamp)

        for time_key in range(start_time, now_timestamp, time_interval):
            swaps_seq_map[pool_id][time_key] = change_seq.get(time_key, 0)

    return swaps_seq_map


def value_with_decimals(value: int, decimals: int) -> float:
    return value / 10**decimals


def calc_liquidity_chart(liquidity_seq: dict[int, float]) -> list[ChartPoint]:
    return calc_chart(liquidity_seq, USD_LIQUIDITY_ROUND_DECIMALS)


def calc_volume_chart(volume_seq: dict[int, float]) -> list[ChartPoint]:
    return calc_chart(volume_seq, USD_VOLUME_ROUND_DECIMALS)


def calc_swaps_chart(swaps_seq: dict[int, int]) -> list[ChartPoint]:
    return calc_chart(swaps_seq)


def calc_chart(seq: dict[int, float] | dict[int, int], decimals: int | None = None) -> list[ChartPoint]:
    return [
        ChartPoint(
            time=datetime.fromtimestamp(timestamp, timezone.utc).strftime("%Y-%m-%d"),
            value=value if decimals is None else round(value, decimals),
        )
        for timestamp, value in sorted(seq.items())
    ]
