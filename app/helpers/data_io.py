"""
Example Data I/O Helper Module

This module demonstrates common data transformation and validation patterns
that are useful when working with database results and API responses.

**Example Usage:**
```python
from ..helpers.data_io import convert_to_type, is_null, get_column_data

# Type conversion
value = convert_to_type(int, "123")  # Returns: 123
value = convert_to_type(float, "12.45")  # Returns: 12.45
value = convert_to_type(str, 789, upper_c=True)  # Returns: "789"

# Null checking
is_null(None)  # Returns: True
is_null("value")  # Returns: False

# Safe column access
data = get_column_data(row, 'latitude', fallback=0.0)
```
"""

from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Type


def convert_to_type(out_type: Type, data: Any, strip: bool = False, upper_c: bool = False) -> Any:
    """
    Convert data to the specified type with error handling.
    
    Args:
        out_type: The target type (int, float, str, bool, etc.)
        data: The data to convert
        strip: Whether to strip whitespace (for strings)
        upper_c: Whether to uppercase (for strings)
    
    Returns:
        Converted value or empty string on error
    
    Examples:
        >>> convert_to_type(int, "42")
        42
        >>> convert_to_type(float, "3.14")
        3.14
        >>> convert_to_type(str, 123, upper_c=True)
        '123'
        >>> convert_to_type(bool, "true")
        True
    """
    try:
        # Handle null/empty values
        if data is None or data == 'NULL' or data == '' or data == 'null':
            return ''

        elif out_type == int:
            return int(data)

        elif out_type == float:
            return float(data)

        elif out_type == str:
            out = str(data)
            if strip:
                out = out.lstrip().rstrip()
            if upper_c:
                out = out.upper()
            return out

        elif out_type == bool:
            if isinstance(data, str):
                return data.lower() in ['true', '1', 'yes']
            return bool(data)

        else:
            return data
    except (ValueError, TypeError):
        return ''


def get_column_data(row: Any, column_name: str, fallback: Any = None) -> Any:
    """
    Safely get column data from a database row with fallback.
    
    Args:
        row: Database row object
        column_name: Name of the column to retrieve
        fallback: Value to return if column is null or missing
    
    Returns:
        Column value or fallback value
    
    Examples:
        >>> get_column_data(airport_row, 'elevation', fallback=0)
        1234
        >>> get_column_data(airport_row, 'missing_column', fallback=-1)
        -1
    """
    try:
        out = getattr(row, column_name)
        if out is None or out == 'NULL':
            return fallback
        return out
    except AttributeError:
        return fallback


def is_null(value: Any) -> bool:
    """
    Check if a value is null or empty.
    
    Args:
        value: The value to check
    
    Returns:
        True if null/empty, False otherwise
    
    Examples:
        >>> is_null(None)
        True
        >>> is_null("NULL")
        True
        >>> is_null("")
        True
        >>> is_null("value")
        False
    """
    return value is None or value == 'NULL' or value == ''


def packager(
    db_result: Iterable[Any],
    *columns: Any,
    defaults: Optional[Dict[str, Any]] = None,
    generator: bool = False,
    exclude: Optional[List[str]] = None,
    group_by: Optional[tuple[str, Callable[[Any], Any]]] = None,
    coordinates: Optional[List[tuple[str, str]]] = None,
    **packets: Any,
) -> List[Dict[str, Any]] | Dict[str, Dict[str, Any]] | Iterator[Dict[str, Any]]:
    """
    Package database query results into a list of dictionaries.

    Positional args (*columns):
        - str: use as key and column name
        - tuple(key, column): use key for dict, column for db lookup

    Keyword args (**packets):
        - Each value is a list of str or tuples like above, forming a nested dict

    defaults: dict
        - default values for keys if DB returns None or missing
        - format: { "key_name": default_value, "nested_key": { "inner_key": default_value } }

    group_by: tuple(column_key, key_formatting_function)
        - Groups results by the given column key
        - Example: ("runway_identifier", lambda x: x.removeprefix("RW"))
    """
    defaults = defaults or {}
    rows = list(db_result)
    packaged: List[Dict[str, Any]] = []

    if exclude is None:
        for row in rows:
            item: Dict[str, Any] = {}

            for col in columns:
                if isinstance(col, tuple):
                    key, col_name = col
                else:
                    key = col_name = col
                default = defaults.get(key, "")
                item[key] = get_column_data(row, col_name, default)

            if coordinates:
                for response_key, db_field in coordinates:
                    item[response_key] = get_column_data(row, db_field, None)

            for packet_name, packet_columns in packets.items():
                temp: Dict[str, Any] = {}
                packet_defaults = defaults.get(packet_name, {})
                for col in packet_columns:
                    if isinstance(col, tuple):
                        key, col_name = col
                    else:
                        key = col_name = col
                    default = packet_defaults.get(key, "")
                    temp[key] = get_column_data(row, col_name, default)
                item[packet_name] = temp

            packaged.append(item)

    else:
        for row in rows:
            item: Dict[str, Any] = {}
            row_columns = getattr(getattr(row, "__table__", None), "columns", None)
            if row_columns is not None:
                columns_all = row_columns.keys()
                for col in columns_all:
                    if col not in exclude:
                        default = defaults.get(col, "")
                        item[col] = get_column_data(row, col, default)

            if coordinates:
                for response_key, db_field in coordinates:
                    item[response_key] = get_column_data(row, db_field, None)

            for packet_name, packet_columns in packets.items():
                temp: Dict[str, Any] = {}
                packet_defaults = defaults.get(packet_name, {})
                for col in packet_columns:
                    if isinstance(col, tuple):
                        key, col_name = col
                    else:
                        key = col_name = col
                    default = packet_defaults.get(key, "")
                    temp[key] = get_column_data(row, col_name, default)
                item[packet_name] = temp

            packaged.append(item)

    # ---- Apply grouping if requested ----
    if group_by:
        col_key, formatter = group_by
        grouped: Dict[str, Dict[str, Any]] = {}
        for item in packaged:
            raw_key = item.get(col_key)
            if raw_key is None:
                continue
            group_key = formatter(raw_key) if formatter else raw_key
            grouped[str(group_key)] = item
        return grouped

    if generator:
        return (p for p in packaged)
    else:
        return packaged
