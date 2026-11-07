import json


def read_public_operator(path):
    """Read owner-confirmed public legal fields from the private deployment."""
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    fields = ("name", "address", "tax_id")
    if not isinstance(data, dict) or any(
        not isinstance(data.get(key), str) or not data[key].strip() for key in fields
    ):
        raise RuntimeError("Public operator configuration is incomplete")
    return {key: data[key].strip() for key in fields}
