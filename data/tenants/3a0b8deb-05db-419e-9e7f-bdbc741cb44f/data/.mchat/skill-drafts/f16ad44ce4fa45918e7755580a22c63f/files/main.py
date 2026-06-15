import csv
import json
import io
from typing import Dict, Any

def run(args: Dict[str, Any]) -> str:
    """
    Convert CSV or JSON text to a Markdown table.
    Args:
        args: Dictionary with key 'input' containing the text.
    Returns:
        Markdown table string.
    """
    text = args.get('input', '').strip()
    if not text:
        return "Error: No input provided."
    
    # Detect format: JSON if starts with '[' or '{'
    if text.startswith('[') or text.startswith('{'):
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON: {e}"
        if isinstance(data, dict):
            data = [data]  # single object -> list of one
        if not isinstance(data, list) or not data:
            return "Error: JSON must be an array of objects."
        # Assume all objects have same keys; use keys from first object
        headers = list(data[0].keys())
        rows = [[str(item.get(h, '')) for h in headers] for item in data]
    else:
        # Treat as CSV
        try:
            reader = csv.reader(io.StringIO(text))
            rows = [row for row in reader]
        except Exception as e:
            return f"Error parsing CSV: {e}"
        if not rows:
            return "Error: No data found."
        headers = rows[0]
        rows = rows[1:]
    
    # Build Markdown table
    header_line = '| ' + ' | '.join(headers) + ' |'
    separator_line = '| ' + ' | '.join(['---'] * len(headers)) + ' |'
    data_lines = ['| ' + ' | '.join(row) + ' |' for row in rows]
    table = '\n'.join([header_line, separator_line] + data_lines)
    return table