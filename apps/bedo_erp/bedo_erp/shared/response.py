def success(data=None, message=None):
    payload = {"ok": True}
    if message:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    return payload


def failure(message):
    return {"ok": False, "message": message}
