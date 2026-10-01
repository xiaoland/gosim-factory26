"""Provider-neutral topology, scope, and usage projections over trajectory v2."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from ..telemetry.trajectory_v2 import (
    ExecutionRecord,
    RelationEvent,
    UsageEvent,
    UsageMeasurement,
    ValidatedTrajectoryV2,
)


@dataclass(frozen=True, slots=True)
class AggregatedMeasurement:
    metric: str
    value: int | float
    unit: str
    inclusion: str
    related_metric: str | None
    currency: str | None
    scope: str
    source: str


@dataclass(frozen=True, slots=True)
class UsageAggregate:
    known: tuple[AggregatedMeasurement, ...]
    ambiguous_observations: int = 0
    unknown_observations: int = 0


def delegation_edges(trajectory: ValidatedTrajectoryV2) -> tuple[RelationEvent, ...]:
    return tuple(
        event
        for event in trajectory.events
        if isinstance(event, RelationEvent) and event.payload.relation == "delegation"
    )


def descendants(trajectory: ValidatedTrajectoryV2, execution_id: str) -> set[str]:
    children: dict[str, set[str]] = defaultdict(set)
    for relation in delegation_edges(trajectory):
        if relation.mapping == "tentative":
            continue
        source = relation.payload.source
        target = relation.payload.target
        if source.type == target.type == "execution":
            children[source.id].add(target.id)
    result: set[str] = set()
    frontier = list(children[execution_id])
    while frontier:
        child = frontier.pop()
        if child in result:
            continue
        result.add(child)
        frontier.extend(children[child])
    return result


def path_event_ids(trajectory: ValidatedTrajectoryV2, leaf_event_id: str) -> set[str]:
    by_id = {event.event_id: event for event in trajectory.events}
    if leaf_event_id not in by_id:
        return set()
    result: set[str] = set()
    frontier = [leaf_event_id]
    while frontier:
        event_id = frontier.pop()
        if event_id in result or event_id not in by_id:
            continue
        result.add(event_id)
        frontier.extend(by_id[event_id].predecessor_ids)
    coordinates = {
        (ref.material, ref.record_id, ref.line)
        for event_id in result
        for ref in by_id[event_id].source_refs
    }
    result.update(
        event.event_id
        for event in trajectory.events
        if any(
            (ref.material, ref.record_id, ref.line) in coordinates
            for ref in event.source_refs
        )
    )
    return result


def _measurement_key(
    event: UsageEvent, measurement: UsageMeasurement
) -> tuple[str, str, str | None, str, str]:
    return (
        measurement.metric,
        measurement.unit,
        measurement.currency,
        event.payload.scope,
        event.payload.source,
    )


def _aggregate_events(events: Iterable[UsageEvent]) -> UsageAggregate:
    samples = tuple(events)
    deduped: list[UsageEvent] = []
    by_sample: dict[str, list[UsageEvent]] = defaultdict(list)
    ambiguous = 0
    for event in samples:
        sample_id = event.payload.sample_id
        if sample_id is None:
            deduped.append(event)
        else:
            by_sample[sample_id].append(event)
    for grouped in by_sample.values():
        first = grouped[0]
        if all(item.payload == first.payload for item in grouped[1:]):
            deduped.append(first)
        else:
            ambiguous += len(grouped)
    groups: dict[
        tuple[str, str, str | None, str, str], list[tuple[UsageEvent, UsageMeasurement]]
    ] = defaultdict(list)
    for event in deduped:
        for measurement in event.payload.measurements:
            groups[_measurement_key(event, measurement)].append((event, measurement))
    known: list[AggregatedMeasurement] = []
    unknown = 0
    conflicting_deltas: set[str] = set()
    for observations in groups.values():
        deltas = [
            item for item in observations if item[0].payload.temporality == "delta"
        ]
        cumulative = [
            item for item in observations if item[0].payload.temporality == "cumulative"
        ]
        delta_by_source = {
            tuple(
                (ref.material, ref.record_id, ref.line) for ref in event.source_refs
            ): (event, measurement)
            for event, measurement in deltas
        }
        previous_by_counter: dict[str, float] = {}
        for event, measurement in cumulative:
            if event.payload.counter_id is None:
                continue
            current = float(measurement.value)
            previous = previous_by_counter.get(event.payload.counter_id)
            coordinate = tuple(
                (ref.material, ref.record_id, ref.line) for ref in event.source_refs
            )
            paired = delta_by_source.get(coordinate)
            if previous is not None and paired is not None:
                expected = current if event.payload.reset else current - previous
                if expected < 0 or float(paired[1].value) != expected:
                    conflicting_deltas.add(paired[0].event_id)
            previous_by_counter[event.payload.counter_id] = current
    for key, observations in sorted(groups.items()):
        deltas = [
            item
            for item in observations
            if item[0].payload.temporality == "delta"
            and item[0].event_id not in conflicting_deltas
        ]
        value = 0.0
        inclusion = observations[0][1].inclusion
        related = observations[0][1].related_metric
        if deltas:
            value = sum(float(item[1].value) for item in deltas)
            delta_coordinates = {
                tuple(
                    (ref.material, ref.record_id, ref.line) for ref in event.source_refs
                )
                for event, _ in deltas
            }
            unknown += sum(
                event.payload.temporality == "cumulative"
                and tuple(
                    (ref.material, ref.record_id, ref.line) for ref in event.source_refs
                )
                not in delta_coordinates
                for event, _ in observations
            )
        else:
            counters: dict[str, list[tuple[UsageEvent, UsageMeasurement]]] = (
                defaultdict(list)
            )
            for item in observations:
                if (
                    item[0].payload.temporality == "cumulative"
                    and item[0].payload.counter_id
                ):
                    counters[item[0].payload.counter_id].append(item)
                elif item[0].payload.temporality in {"gauge", "unknown"}:
                    unknown += 1
            for sequence in counters.values():
                previous: float | None = None
                for event, measurement in sequence:
                    current = float(measurement.value)
                    if previous is None:
                        if event.payload.zero_baseline:
                            value += current
                        else:
                            unknown += 1
                    elif event.payload.reset:
                        value += current
                    elif current >= previous:
                        value += current - previous
                    else:
                        ambiguous += 1
                    previous = current
        if value or any(float(item[1].value) == 0 for item in observations):
            known.append(
                AggregatedMeasurement(
                    metric=key[0],
                    value=int(value) if value.is_integer() else value,
                    unit=key[1],
                    inclusion=inclusion,
                    related_metric=related,
                    currency=key[2],
                    scope=key[3],
                    source=key[4],
                )
            )
    return UsageAggregate(tuple(known), ambiguous + len(conflicting_deltas), unknown)


def usage_for_execution(
    trajectory: ValidatedTrajectoryV2,
    execution_id: str,
    *,
    inclusive: bool = False,
    event_ids: set[str] | None = None,
) -> UsageAggregate:
    owners = {execution_id}
    if inclusive:
        owners |= descendants(trajectory, execution_id)
    selected: list[UsageEvent] = []
    events_by_id = {event.event_id: event for event in trajectory.events}
    for event in trajectory.events:
        if not isinstance(event, UsageEvent):
            continue
        if event_ids is not None and event.event_id not in event_ids:
            owner = event.payload.owner
            if owner.type != "event" or owner.id not in event_ids:
                continue
        owner = event.payload.owner
        owner_execution = event.execution_id
        if owner.type == "execution":
            owner_execution = owner.id
        elif owner.type == "event" and owner.id in events_by_id:
            owner_execution = events_by_id[owner.id].execution_id
        if owner_execution in owners and event.mapping != "tentative":
            selected.append(event)
    return _aggregate_events(selected)


def aggregate_usage(events: Iterable[UsageEvent]) -> UsageAggregate:
    return _aggregate_events(events)


def execution_lifecycle(trajectory: ValidatedTrajectoryV2, execution_id: str) -> str:
    transitions = [
        event.payload.transition
        for event in trajectory.events
        if event.kind == "lifecycle" and event.execution_id == execution_id
    ]
    if "error" in transitions:
        return "error"
    if "cancel" in transitions:
        return "cancelled"
    if "complete" in transitions:
        return "complete"
    if "start" in transitions:
        return "running"
    return "unknown"


def execution_by_id(trajectory: ValidatedTrajectoryV2) -> dict[str, ExecutionRecord]:
    return {item.execution_id: item for item in trajectory.executions}


__all__ = [
    "UsageAggregate",
    "AggregatedMeasurement",
    "aggregate_usage",
    "delegation_edges",
    "descendants",
    "execution_by_id",
    "execution_lifecycle",
    "path_event_ids",
    "usage_for_execution",
]
