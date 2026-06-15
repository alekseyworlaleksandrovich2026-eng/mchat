import json
import csv
import io

def run(args: dict) -> str:
    """
    Convert JSON or CSV data to a Markdown table.
    Args: data (str) - the input data string.
    Returns: Markdown table string.
    """
    data = args.get("data", "")
    if not data:
        return "No data provided."
    
    # Try to parse as JSON first
    try:
        parsed = json.loads(data)
        if isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], dict):
            rows = parsed
            if not rows:
                return "Empty data."
            headers = list(rows[0].keys())
            table = [headers]
            for row in rows:
                table.append([str(row.get(h, "")) for h in headers])
        elif isinstance(parsed, dict):
            rows = [parsed]
            headers = list(parsed.keys())
            table = [headers]
            table.append([str(parsed[h]) for h in headers])
        else:
            return "Unsupported JSON structure. Need array of objects or object."
    except json.JSONDecodeError:
        # Attempt CSV
        try:
            reader = csv.DictReader(io.StringIO(data))
            rows = list(reader)
            if not rows:
                return "Empty CSV data."
            headers = reader.fieldnames
            table = [headers]
            for row in rows:
                table.append([str(row.get(h, "")) for h in headers])
        except Exception:
            return "Unable to parse input as JSON or CSV."
    
    # Format as Markdown table
    col_widths = [max(len(str(row[i])) for row in table) for i in range(len(headers))]
    separator = ["-" * w for w in col_widths]
    formatted = []
    formatted.append("| " + " | ".join(headers[i].ljust(col_widths[i]) for i in range(len(headers))) + " |")
    formatted.append("| " + " | ".join(separator) + " |")
    for row in table[1:]:
        formatted.append("| " + " | ".join(row[i].ljust(col_widths[i]) for i in range(len(headers))) + " |")
    return "\n".join(formatted)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            print(run({"data": f.read()}))
    else:
        print("Usage: python main.py <input_file>")
