def run(**kwargs):
    name = kwargs.get("name", "tenant1")
    return {"message": f"Hello {name} from sidecar", "args": kwargs}
