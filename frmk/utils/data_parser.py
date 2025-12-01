"""
Data Parsing Utilities
Common functions for parsing and formatting tool results
"""

from typing import Dict, Any, List, Optional, Union
import json
from datetime import datetime, date
from decimal import Decimal


def parse_sql_results(results: Dict[str, Any], format: str = "markdown") -> str:
    """
    Parse SQL query results into human-readable format

    Args:
        results: ToolOutput.data from SQLTool
        format: Output format ('markdown', 'json', 'text')

    Returns:
        Formatted string
    """

    if not results.get("rows"):
        return "No results found."

    rows = results["rows"]
    columns = results.get("columns", [])
    truncated = results.get("truncated", False)

    if format == "markdown":
        return _format_table_markdown(rows, columns, truncated)
    elif format == "json":
        return json.dumps(rows, indent=2, default=str)
    elif format == "text":
        return _format_table_text(rows, columns, truncated)
    else:
        raise ValueError(f"Unsupported format: {format}")


def _format_table_markdown(rows: List[Dict], columns: List[str], truncated: bool) -> str:
    """Format as Markdown table"""

    if not rows:
        return "No results."

    # Header
    lines = []
    lines.append("| " + " | ".join(columns) + " |")
    lines.append("| " + " | ".join(["---"] * len(columns)) + " |")

    # Rows
    for row in rows:
        values = [str(row.get(col, "")) for col in columns]
        lines.append("| " + " | ".join(values) + " |")

    if truncated:
        lines.append(f"\n*Results truncated (showing {len(rows)} rows)*")

    return "\n".join(lines)


def _format_table_text(rows: List[Dict], columns: List[str], truncated: bool) -> str:
    """Format as plain text table"""

    if not rows:
        return "No results."

    # Calculate column widths
    widths = {col: len(col) for col in columns}
    for row in rows:
        for col in columns:
            widths[col] = max(widths[col], len(str(row.get(col, ""))))

    # Header
    lines = []
    header = " | ".join(col.ljust(widths[col]) for col in columns)
    lines.append(header)
    lines.append("-" * len(header))

    # Rows
    for row in rows:
        values = [str(row.get(col, "")).ljust(widths[col]) for col in columns]
        lines.append(" | ".join(values))

    if truncated:
        lines.append(f"\nResults truncated (showing {len(rows)} rows)")

    return "\n".join(lines)


def parse_vector_results(results: Dict[str, Any], include_scores: bool = True) -> str:
    """
    Parse vector search results into readable format

    Args:
        results: ToolOutput.data from VectorDBTool
        include_scores: Include relevance scores

    Returns:
        Formatted string
    """

    if not results.get("results"):
        return "No relevant documents found."

    docs = results["results"]
    lines = []

    lines.append(f"Found {results.get('count', len(docs))} relevant documents:\n")

    for i, doc in enumerate(docs, 1):
        lines.append(f"**Result {i}**")

        if include_scores and "score" in doc:
            score = doc["score"]
            lines.append(f"Relevance: {score:.2%}")

        # Content
        content = doc.get("content") or doc.get("payload", {}).get("content", "")
        if content:
            preview = content[:200] + "..." if len(content) > 200 else content
            lines.append(f"```\n{preview}\n```")

        # Metadata
        metadata = doc.get("metadata", {})
        if metadata:
            lines.append(f"Metadata: {json.dumps(metadata, default=str)}")

        lines.append("")  # Blank line

    return "\n".join(lines)


def parse_http_json_response(response_data: Any, path: Optional[str] = None) -> Any:
    """
    Parse JSON response from HTTP tool

    Args:
        response_data: Response data (dict, list, or primitive)
        path: Optional JSONPath expression to extract specific data

    Returns:
        Extracted data
    """

    if path is None:
        return response_data

    # Simple dot-notation path support (e.g., "data.items[0].name")
    parts = path.replace("[", ".").replace("]", "").split(".")
    current = response_data

    for part in parts:
        if not part:
            continue

        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            try:
                index = int(part)
                current = current[index]
            except (ValueError, IndexError):
                return None
        else:
            return None

    return current


def format_currency(amount: Union[float, Decimal, str], currency: str = "USD") -> str:
    """
    Format currency value

    Args:
        amount: Numeric amount
        currency: Currency code (USD, EUR, etc.)

    Returns:
        Formatted string (e.g., "$1,234.56")
    """

    try:
        value = float(amount)

        # Currency symbols
        symbols = {
            "USD": "$",
            "EUR": "€",
            "GBP": "£",
            "JPY": "¥",
            "CNY": "¥"
        }

        symbol = symbols.get(currency, currency + " ")

        # Format with thousand separators
        if currency == "JPY":
            # No decimal places for JPY
            return f"{symbol}{value:,.0f}"
        else:
            return f"{symbol}{value:,.2f}"

    except (ValueError, TypeError):
        return str(amount)


def format_date(date_value: Union[str, datetime, date], format: str = "readable") -> str:
    """
    Format date value

    Args:
        date_value: Date string, datetime, or date object
        format: Output format ('readable', 'iso', 'short')

    Returns:
        Formatted date string
    """

    if isinstance(date_value, str):
        try:
            # Try parsing common formats
            for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                try:
                    date_value = datetime.strptime(date_value, fmt)
                    break
                except ValueError:
                    continue
        except:
            return date_value

    if isinstance(date_value, datetime):
        dt = date_value
    elif isinstance(date_value, date):
        dt = datetime.combine(date_value, datetime.min.time())
    else:
        return str(date_value)

    if format == "readable":
        return dt.strftime("%B %d, %Y")  # "January 15, 2025"
    elif format == "iso":
        return dt.isoformat()
    elif format == "short":
        return dt.strftime("%m/%d/%Y")  # "01/15/2025"
    else:
        return str(date_value)


def format_list(items: List[Any], style: str = "bullet") -> str:
    """
    Format list of items

    Args:
        items: List of items
        style: 'bullet', 'numbered', or 'comma'

    Returns:
        Formatted string
    """

    if not items:
        return ""

    if style == "bullet":
        return "\n".join(f"• {item}" for item in items)
    elif style == "numbered":
        return "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1))
    elif style == "comma":
        return ", ".join(str(item) for item in items)
    else:
        return "\n".join(str(item) for item in items)


def extract_summary_stats(rows: List[Dict], numeric_columns: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Calculate summary statistics from SQL results

    Args:
        rows: List of row dictionaries
        numeric_columns: Columns to analyze (auto-detect if None)

    Returns:
        Dictionary of statistics
    """

    if not rows:
        return {"count": 0}

    stats = {
        "count": len(rows)
    }

    # Auto-detect numeric columns if not provided
    if numeric_columns is None:
        numeric_columns = []
        first_row = rows[0]
        for col, value in first_row.items():
            if isinstance(value, (int, float, Decimal)):
                numeric_columns.append(col)

    # Calculate stats for each numeric column
    for col in numeric_columns:
        values = [float(row[col]) for row in rows if row.get(col) is not None]

        if values:
            stats[col] = {
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "sum": sum(values)
            }

    return stats


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length

    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add when truncated

    Returns:
        Truncated text
    """

    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix
