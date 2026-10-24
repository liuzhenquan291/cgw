import os
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from admin_page import ADMIN_HTML
from desktop_sync import DesktopSync
from profile_manager import ProfileManager

app = FastAPI()

profiles = ProfileManager()
desktop = DesktopSync()


# ── API endpoints (Claude Desktop) ──────────────────────


@app.get("/v1/models")
async def models():
    model_list = profiles.get_active_models()
    return {
        "data": [
            {
                "id": m["id"],
                "object": "model",
                "display_name": m.get("display_name", m["id"]),
            }
            for m in model_list
        ]
    }


@app.post("/v1/messages")
async def messages(request: Request):
    body = await request.json()

    requested_model = body.get("model")
    upstream_model = profiles.get_upstream_model(requested_model)

    if not upstream_model:
        return JSONResponse(
            status_code=400,
            content={
                "type": "error",
                "error": {
                    "type": "invalid_request_error",
                    "message": "Unsupported model: {}".format(requested_model),
                },
            },
        )

    body["model"] = upstream_model

    upstream_url = profiles.get_active_upstream()
    api_key = profiles.get_active_api_key()
    auth_scheme = profiles.get_active_auth_scheme()

    if not upstream_url or not api_key:
        return JSONResponse(
            status_code=500,
            content={
                "type": "error",
                "error": {
                    "type": "api_error",
                    "message": "No active profile configured",
                },
            },
        )

    headers = {
        "content-type": "application/json",
        "anthropic-version": request.headers.get("anthropic-version", "2023-06-01"),
    }

    if auth_scheme == "Authorization":
        headers["Authorization"] = "Bearer " + api_key
    elif auth_scheme == "x-api-key":
        headers["x-api-key"] = api_key
    else:
        headers["api-key"] = api_key

    for header_name in ("anthropic-beta", "user-agent", "x-app"):
        value = request.headers.get(header_name)
        if value:
            headers[header_name] = value

    full_url = "{}/v1/messages".format(upstream_url.rstrip("/"))
    stream = bool(body.get("stream"))
    client = httpx.AsyncClient(timeout=None)

    try:
        if stream:
            upstream_request = client.build_request("POST", full_url, headers=headers, json=body)
            upstream_response = await client.send(upstream_request, stream=True)

            if upstream_response.status_code >= 400:
                content = await upstream_response.aread()
                await upstream_response.aclose()
                await client.aclose()
                return Response(
                    content=content,
                    status_code=upstream_response.status_code,
                    media_type=upstream_response.headers.get("content-type", "application/json"),
                )

            async def iterator():
                try:
                    async for chunk in upstream_response.aiter_raw():
                        yield chunk
                finally:
                    await upstream_response.aclose()
                    await client.aclose()

            return StreamingResponse(
                iterator(),
                status_code=upstream_response.status_code,
                media_type=upstream_response.headers.get("content-type", "text/event-stream"),
                headers={"cache-control": "no-cache", "connection": "keep-alive"},
            )

        upstream_response = await client.post(full_url, headers=headers, json=body)
        content = upstream_response.content
        content_type = upstream_response.headers.get("content-type", "application/json")
        await client.aclose()
        return Response(
            content=content,
            status_code=upstream_response.status_code,
            media_type=content_type,
        )

    except Exception:
        await client.aclose()
        raise


@app.get("/health")
async def health():
    return {"ok": True}


# ── Admin web page ──────────────────────────────────────


@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    return HTMLResponse(ADMIN_HTML)


# ── Admin API: status ───────────────────────────────────


@app.get("/admin/api/status")
async def admin_status():
    active = profiles.get_active_profile()
    return {
        "ok": True,
        "model_count": len(profiles.get_active_models()),
        "active_profile": active.get("name") if active else None,
        "upstream_base_url": active.get("upstream_url") if active else None,
        "config_path": profiles._path,
        "config_error": None,
    }


# ── Admin API: models ───────────────────────────────────


@app.get("/admin/api/models")
async def admin_list_models():
    active = profiles.get_active_profile()
    models = active.get("models", []) if active else []
    result = []
    for m in models:
        result.append({
            "id": m["id"],
            "upstream": m["upstream"],
            "display_name": m.get("display_name", m["id"]),
        })
    return {"models": result, "profile": active.get("name") if active else None}


@app.post("/admin/api/models")
async def admin_add_model(request: Request):
    body = await request.json()
    active = profiles.get_active_profile()
    if not active:
        return JSONResponse(status_code=400, content={"detail": "No active profile"})
    try:
        profiles.add_model_to_profile(
            active["name"],
            body.get("id", ""),
            body.get("upstream", ""),
            body.get("display_name", ""),
        )
        return JSONResponse(status_code=201, content={"ok": True})
    except ValueError as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    except KeyError as e:
        return JSONResponse(status_code=409, content={"detail": str(e)})


@app.put("/admin/api/models/{model_id}")
async def admin_update_model(model_id: str, request: Request):
    body = await request.json()
    new_id = body.get("id")
    if new_id and new_id != model_id:
        return JSONResponse(status_code=400, content={"detail": "Model ID cannot be changed."})
    active = profiles.get_active_profile()
    if not active:
        return JSONResponse(status_code=400, content={"detail": "No active profile"})
    try:
        profiles.update_model_in_profile(
            active["name"], model_id,
            upstream=body.get("upstream"),
            display_name=body.get("display_name"),
        )
        return {"ok": True}
    except ValueError as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    except KeyError as e:
        return JSONResponse(status_code=404, content={"detail": str(e)})


@app.delete("/admin/api/models/{model_id}")
async def admin_delete_model(model_id: str):
    active = profiles.get_active_profile()
    if not active:
        return JSONResponse(status_code=400, content={"detail": "No active profile"})
    try:
        profiles.remove_model_from_profile(active["name"], model_id)
        return {"ok": True}
    except KeyError as e:
        return JSONResponse(status_code=404, content={"detail": str(e)})


# ── Admin API: profiles ─────────────────────────────────


@app.get("/admin/api/profiles")
async def admin_list_profiles():
    return profiles.list_profiles()


@app.post("/admin/api/profiles")
async def admin_add_profile(request: Request):
    body = await request.json()
    try:
        result = profiles.add_profile(
            name=body.get("name", ""),
            upstream_url=body.get("upstream_url", ""),
            api_key=body.get("api_key", ""),
            models=body.get("models"),
            auth_scheme=body.get("auth_scheme", "api-key"),
        )
        return JSONResponse(status_code=201, content={"profile": result})
    except ValueError as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    except KeyError as e:
        return JSONResponse(status_code=409, content={"detail": str(e)})


@app.put("/admin/api/profiles/{name}")
async def admin_update_profile(name: str, request: Request):
    body = await request.json()
    try:
        result = profiles.update_profile(
            name,
            upstream_url=body.get("upstream_url"),
            api_key=body.get("api_key"),
            auth_scheme=body.get("auth_scheme"),
        )
        return {"profile": result}
    except ValueError as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    except KeyError as e:
        return JSONResponse(status_code=404, content={"detail": str(e)})


@app.delete("/admin/api/profiles/{name}")
async def admin_delete_profile(name: str):
    try:
        profiles.delete_profile(name)
        return {"ok": True}
    except KeyError as e:
        return JSONResponse(status_code=404, content={"detail": str(e)})


@app.post("/admin/api/profiles/switch")
async def admin_switch_profile(request: Request):
    body = await request.json()
    name = body.get("name", "")
    try:
        result = profiles.switch_profile(name)
        return {"ok": True, "profile": result, "message": "Please restart gateway to apply"}
    except KeyError as e:
        return JSONResponse(status_code=404, content={"detail": str(e)})


# ── Admin API: Claude Desktop sync ──────────────────────


@app.get("/admin/api/desktop/status")
async def admin_desktop_status():
    return desktop.get_status()


@app.post("/admin/api/desktop/sync")
async def admin_desktop_sync():
    if not desktop.is_installed():
        return JSONResponse(status_code=400, content={"detail": "Claude Desktop not installed"})
    active = profiles.get_active_profile()
    if not active:
        return JSONResponse(status_code=400, content={"detail": "No active profile"})
    models = [
        {"id": m["id"], "display_name": m.get("display_name", m["id"])}
        for m in active.get("models", [])
    ]
    result = desktop.sync_from_gateway(models, active.get("api_key", ""))
    return {"ok": True, "result": result}


@app.post("/admin/api/desktop/import")
async def admin_desktop_import():
    if not desktop.is_installed():
        return JSONResponse(status_code=400, content={"detail": "Claude Desktop not installed"})
    models = desktop.sync_to_gateway()
    if not models:
        return JSONResponse(status_code=400, content={"detail": "No config found in Claude Desktop"})
    return {"ok": True, "models": models}


@app.post("/admin/api/desktop/apply")
async def admin_desktop_apply():
    if not desktop.is_installed():
        return JSONResponse(status_code=400, content={"detail": "Claude Desktop not installed"})
    return desktop.apply_and_restart()


@app.post("/admin/api/desktop/discard")
async def admin_desktop_discard():
    desktop.discard_pending()
    return {"ok": True}
