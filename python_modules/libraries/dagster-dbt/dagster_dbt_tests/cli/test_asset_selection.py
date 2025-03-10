from typing import Optional, Set

import pytest
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.events import AssetKey
from dagster._utils import file_relative_path
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.cli.resources_v2 import DbtManifest

manifest_path = file_relative_path(__file__, "../sample_manifest.json")
manifest = DbtManifest.read(path=manifest_path)


@pytest.mark.parametrize(
    ["select", "exclude", "expected_asset_names"],
    [
        (
            "fqn:*",
            None,
            {
                "sort_by_calories",
                "cold_schema/sort_cold_cereals_by_calories",
                "subdir_schema/least_caloric",
                "sort_hot_cereals_by_calories",
                "orders_snapshot",
                "cereals",
            },
        ),
        (
            "+least_caloric",
            None,
            {"sort_by_calories", "subdir_schema/least_caloric", "cereals"},
        ),
        (
            "sort_by_calories least_caloric",
            None,
            {"sort_by_calories", "subdir_schema/least_caloric"},
        ),
        (
            "tag:bar+",
            None,
            {
                "sort_by_calories",
                "cold_schema/sort_cold_cereals_by_calories",
                "subdir_schema/least_caloric",
                "sort_hot_cereals_by_calories",
                "orders_snapshot",
            },
        ),
        (
            "tag:foo",
            None,
            {"sort_by_calories", "cold_schema/sort_cold_cereals_by_calories"},
        ),
        (
            "tag:foo,tag:bar",
            None,
            {"sort_by_calories"},
        ),
        (
            None,
            "sort_hot_cereals_by_calories",
            {
                "sort_by_calories",
                "cold_schema/sort_cold_cereals_by_calories",
                "subdir_schema/least_caloric",
                "cereals",
                "orders_snapshot",
            },
        ),
        (
            None,
            "+least_caloric",
            {
                "cold_schema/sort_cold_cereals_by_calories",
                "sort_hot_cereals_by_calories",
                "orders_snapshot",
            },
        ),
        (
            None,
            "sort_by_calories least_caloric",
            {
                "cold_schema/sort_cold_cereals_by_calories",
                "sort_hot_cereals_by_calories",
                "orders_snapshot",
                "cereals",
            },
        ),
        (
            None,
            "tag:foo",
            {
                "subdir_schema/least_caloric",
                "sort_hot_cereals_by_calories",
                "orders_snapshot",
                "cereals",
            },
        ),
    ],
)
def test_dbt_asset_selection(
    select: Optional[str], exclude: Optional[str], expected_asset_names: Set[str]
) -> None:
    expected_asset_keys = {AssetKey(key.split("/")) for key in expected_asset_names}

    @dbt_assets(manifest=manifest)
    def my_dbt_assets():
        ...

    asset_graph = AssetGraph.from_assets([my_dbt_assets])
    asset_selection = manifest.build_asset_selection(
        dbt_select=select or "fqn:*",
        dbt_exclude=exclude,
    )
    selected_asset_keys = asset_selection.resolve(all_assets=asset_graph)

    assert selected_asset_keys == expected_asset_keys
