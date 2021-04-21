from typing import List


def columns_map_filter_allowed_columns(columns_map: dict, allowed_columns: List) -> dict:
    properties = {}

    for property_name, column_info in columns_map.items():
        if property_name not in allowed_columns:
            continue
        properties[property_name] = column_info

    return properties
