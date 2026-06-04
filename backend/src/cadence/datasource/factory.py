"""Pick the active data + deal source from config: seed (default) or live LakeB2B."""

from __future__ import annotations

from cadence.config import Settings
from cadence.datasource.base import DataSource, DealSource


def get_sources(settings: Settings) -> tuple[DataSource, DealSource]:
    if settings.active_data_source == "lakeb2b":
        from cadence.datasource.lakeb2b_source import LakeB2BDataSource, LakeB2BDealSource

        return (
            LakeB2BDataSource(settings.lakeb2b_api_key, settings.lakeb2b_base_url),
            LakeB2BDealSource(),
        )

    from cadence.datasource.seed_source import SeedDataSource, SeedDealSource
    from cadence.seed.universe import build_universe

    universe = build_universe()
    return SeedDataSource(universe), SeedDealSource(universe)
