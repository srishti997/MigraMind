"""Current synthetic-only API; historical implementation is legacy_adapter.py."""
from authority import (SyntheticDatabase, SyntheticHandle, ReservationAdapter, Decision,
                       StorageUnavailable, StorageBusy, ContinuityLost, GuardRejected,
                       ElapsedClock, Ownership, WINDOW_MS, MAX_CLOCK)
from legacy_adapter import synthetic_keys
