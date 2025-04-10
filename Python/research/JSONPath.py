from jsonpath_ng import parse
import re

# Sample JSON data
data = {
    "store": {
        "book": [
            {
                "category": "reference",
                "author": "Nigel Rees",
                "title": "Sayings of the Century",
                "price": 8.95,
            },
            {
                "category": "fiction",
                "author": "Evelyn Waugh",
                "title": "Sword of Honour",
                "price": 12.99,
            },
            {
                "category": "fiction",
                "author": "Herman Melville",
                "title": "Moby Dick",
                "isbn": "0-553-21311-3",
                "price": 8.99,
            },
            {
                "category": "fiction",
                "author": "J. R. R. Tolkien",
                "title": "The Lord of the Rings",
                "isbn": "0-395-19395-8",
                "price": 22.99,
            },
        ],
        "bicycle": {"color": "red", "price": 399},
    }
}


def flatten(results):
    """Flatten nested lists into a single list."""
    flat = []
    for item in results:
        if isinstance(item, list):
            flat.extend(flatten(item))
        else:
            flat.append(item)
    return flat


def recursive_descent(data, key=None, handle_normal=True):
    """
    Traverse the JSON structure recursively to find all instances of a given key.
    If no key is provided, collect all elements (for recursive wildcards like $..*).
    """
    if handle_normal and key:
        query = f"$..{key}" if key != "*" else "$..*"
        try:
            jsonpath_expr = parse(query)
            result = [match.value for match in jsonpath_expr.find(data)]
            return result
        except Exception:
            pass  # Fallback to explicit handling if JSONPath fails

    results = []
    if isinstance(data, dict):
        for k, v in data.items():
            if key is None or k == key:
                results.append(v)
            results.extend(recursive_descent(v, key, handle_normal=False))
    elif isinstance(data, list):
        for item in data:
            results.extend(recursive_descent(item, key, handle_normal=False))
    return results


def manual_filter(data, condition):
    """
    Apply a manual filter condition (e.g., @.price < 10) to a list of items.
    Safely evaluates the condition for dictionary items.
    """
    filtered = []
    for item in data:
        if isinstance(item, dict):
            try:
                # Replace @.key with item['key'] dynamically for safe access
                condition_replaced = re.sub(r"@\.(\w+)", r'item["\1"]', condition)
                if eval(condition_replaced):
                    filtered.append(item)
            except (KeyError, AttributeError, SyntaxError):
                # Skip items where the condition cannot be applied
                pass
    return filtered


def process_query(query, data):
    pattern = r"\[\d*(:\d*)?(:\d*)?\]"
    match = re.fullmatch(pattern, query) 
    unsupported = any(op in query for op in [":", "..", "[?"])
    if match or not unsupported:
        jsonpath_expr = parse(query)
        result = [match.value for match in jsonpath_expr.find(data)]
        return result
    elif "$..*"==query:
        return recursive_descent(data)
    """
    Process a JSONPath query, supporting normal processing, recursive descent,
    slicing, and filtering.
    """
    if "$.." in query:
        if "[?" in query:
            # Handle filtering
            key = query.split("..")[-1].split("[")[0]
            condition = query.split("[?")[-1].rstrip("]")
            items = flatten(recursive_descent(data, key))
            return manual_filter(items, condition)
        elif "[" in query and ":" in query:
            # Handle slicing
            key = query.split("..")[-1].split("[")[0]
            slice_expr = query.split("[")[-1].rstrip("]")
            start, end = (slice_expr.split(":") + [None])[:2]
            start = int(start) if start else None
            end = int(end) if end else None
            items = flatten(recursive_descent(data, key))
            return items[start:end]
        elif "[" in query:
            # Handle single index
            key = query.split("..")[-1].split("[")[0]
            index = int(query.split("[")[-1].rstrip("]"))
            items = flatten(recursive_descent(data, key))
            return [items[index]] if -len(items) <= index < len(items) else []
        else:
            # Handle recursive descent without filters
            key = query.split("..")[-1].split("[")[0]
            return flatten(recursive_descent(data, key))
    else:
        # Normal JSONPath processing
        try:
            jsonpath_expr = parse(query)
            return [match.value for match in jsonpath_expr.find(data)]
        except Exception as e:
            return f"Error: {e}"

# Test cases
queries = [
    {"query": "$.store.book[*]", "description": "1. All books"},
    {"query": "$.store.book[*].author", "description": "2. Authors of all books"},
    {"query": "$..author", "description": "3. All authors in the document (recursive descent)"},
    {"query": "$..book[2]", "description": "4. The third book"},
    {"query": "$..book[-1]", "description": "5. The last book (negative index)"},
    {"query": "$..book[:2]", "description": "6. The first two books"},
    {"query": "$..book[1:3]", "description": "7. The second and the third books"},
    {"query": "$.store..price", "description": "8. All prices in a store"},
    {"query": "$..book[?@.price<10]", "description": "9. Filter books cheaper than 10"},
    {"query": "$..*", "description": "10. All elements recursively"},
]

for test in queries:
    print(f"Test: {test['description']}")
    result = process_query(test["query"], data)
    print(f"Query: {test['query']}\nResult: {result}\n")
