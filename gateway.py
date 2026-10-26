import os
import signal
import sys
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from admin_page import ADMIN_HTML
from desktop_sync import DesktopSync
from profile_manager import ProfileManager


async def parse_json_body(request):
    """Parse JSON body, return (body, None) on success or (None, error_response) on failure."""
    try:
        body = await request.json()
        if not isinstance(body, dict):
            return None, JSONResponse(status_code=400, content={"detail": "Request body must be a JSON object"})
        # Coerce string fields to str to prevent AttributeError on non-string values
        for key in ("id", "name", "upstream", "upstream_url", "api_key", "auth_scheme", "display_name", "notes"):
            if key in body and body[key] is not None:
                body[key] = str(body[key])
        return body, None
    except ValueError:
        return None, JSONResponse(status_code=400, content={"detail": "Invalid JSON in request body"})


def mask_api_key(key):
    """Mask an API key for display: show only first 4 and last 4 chars."""
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return key[:4] + "..." + key[-4:]


def mask_profile_keys(data):
    """Return a copy of profile data with API keys masked."""
    import copy
    result = copy.deepcopy(data)
    for p in result.get("profiles", {}).values():
        if isinstance(p, dict) and "api_key" in p:
            p["api_key"] = mask_api_key(p["api_key"])
    return result


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
                "id": m.get("id", ""),
                "object": "model",
                "display_name": m.get("display_name") or m.get("id", ""),
            }
            for m in model_list
            if isinstance(m, dict) and m.get("id")
        ]
    }


@app.post("/v1/messages")
async def messages(request: Request):
    body, err = await parse_json_body(request)
    if err:
        return err

    requested_model = body.get("model")
    if not requested_model:
        return JSONResponse(
            status_code=400,
            content={
                "type": "error",
                "error": {
                    "type": "invalid_request_error",
                    "message": "Missing 'model' field in request body",
                },
            },
        )

    # Get active profile once to avoid race conditions
    active = profiles.get_active_profile()
    if not active or not active.get("upstream_url") or not active.get("api_key"):
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

    # Find upstream model from the active profile's model list
    upstream_model = None
    for m in active.get("models", []):
        if m.get("id") == requested_model:
            upstream_model = m.get("upstream")
            break

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
    upstream_url = active["upstream_url"]
    api_key = active["api_key"]
    auth_scheme = active.get("auth_scheme", "api-key")

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
        try:
            await client.aclose()
        except Exception:
            pass
        raise


@app.get("/health")
async def health():
    return {"ok": True}


@app.post("/admin/api/gateway/restart")
async def admin_gateway_restart():
    # Schedule restart in background so we can return response first
    import threading, time

    def _restart():
        time.sleep(0.5)
        # Kill all processes on our port
        try:
            import subprocess
            out = subprocess.check_output(["lsof", "-ti", ":8787"], stderr=subprocess.DEVNULL)
            for p in out.strip().split(b"\n"):
                if p:
                    try:
                        os.kill(int(p), signal.SIGKILL)
                    except (ProcessLookupError, PermissionError):
                        pass
        except Exception:
            pass
        time.sleep(0.5)
        # Re-exec uvicorn
        os.execv(sys.executable, [sys.executable, "-m", "uvicorn", "gateway:app",
                                   "--host", "127.0.0.1", "--port", "8787"])

    threading.Thread(target=_restart, daemon=True).start()
    return {"ok": True, "message": "Gateway restarting..."}


# ── Admin web page ──────────────────────────────────────


@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    return HTMLResponse(ADMIN_HTML)


# ── Admin API: status ───────────────────────────────────


@app.get("/admin/api/status")
async def admin_status():
    active = profiles.get_active_profile()
    all_data = profiles.list_profiles()
    return {
        "ok": all_data.get("config_error") is None,
        "model_count": len(profiles.get_active_models()),
        "active_profile": active.get("name") if active else None,
        "upstream_base_url": active.get("upstream_url") if active else None,
        "config_path": profiles.path,
        "config_error": all_data.get("config_error"),
    }


# ── Admin API: models ───────────────────────────────────


@app.get("/admin/api/models")
async def admin_list_models():
    active = profiles.get_active_profile()
    models = active.get("models", []) if active else []
    if not isinstance(models, list):
        models = []
    result = []
    for m in models:
        if not isinstance(m, dict):
            continue
        result.append({
            "id": m.get("id", ""),
            "upstream": m.get("upstream", ""),
            "display_name": m.get("display_name") or m.get("id", ""),
        })
    return {"models": result, "profile": active.get("name") if active else None}


@app.post("/admin/api/models")
async def admin_add_model(request: Request):
    body, err = await parse_json_body(request)
    if err:
        return err
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
        return JSONResponse(status_code=400, content={"detail": str(e.args[0]) if e.args else str(e)})
    except KeyError as e:
        return JSONResponse(status_code=409, content={"detail": str(e.args[0]) if e.args else str(e)})


@app.put("/admin/api/models/{model_id}")
async def admin_update_model(model_id: str, request: Request):
    body, err = await parse_json_body(request)
    if err:
        return err
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
        return JSONResponse(status_code=400, content={"detail": str(e.args[0]) if e.args else str(e)})
    except KeyError as e:
        return JSONResponse(status_code=404, content={"detail": str(e.args[0]) if e.args else str(e)})


@app.delete("/admin/api/models/{model_id}")
async def admin_delete_model(model_id: str):
    active = profiles.get_active_profile()
    if not active:
        return JSONResponse(status_code=400, content={"detail": "No active profile"})
    try:
        profiles.remove_model_from_profile(active["name"], model_id)
        return {"ok": True}
    except KeyError as e:
        return JSONResponse(status_code=404, content={"detail": str(e.args[0]) if e.args else str(e)})


# ── Admin API: profiles ─────────────────────────────────


@app.get("/admin/api/profiles")
async def admin_list_profiles():
    return mask_profile_keys(profiles.list_profiles())


@app.post("/admin/api/profiles")
async def admin_add_profile(request: Request):
    body, err = await parse_json_body(request)
    if err:
        return err
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
        return JSONResponse(status_code=400, content={"detail": str(e.args[0]) if e.args else str(e)})
    except KeyError as e:
        return JSONResponse(status_code=409, content={"detail": str(e.args[0]) if e.args else str(e)})


@app.put("/admin/api/profiles/{name}")
async def admin_update_profile(name: str, request: Request):
    body, err = await parse_json_body(request)
    if err:
        return err
    try:
        result = profiles.update_profile(
            name,
            upstream_url=body.get("upstream_url"),
            api_key=body.get("api_key"),
            auth_scheme=body.get("auth_scheme"),
        )
        if isinstance(result, dict) and "api_key" in result:
            result["api_key"] = mask_api_key(result["api_key"])
        return {"profile": result}
    except ValueError as e:
        return JSONResponse(status_code=400, content={"detail": str(e.args[0]) if e.args else str(e)})
    except KeyError as e:
        return JSONResponse(status_code=404, content={"detail": str(e.args[0]) if e.args else str(e)})


@app.delete("/admin/api/profiles/{name}")
async def admin_delete_profile(name: str):
    try:
        profiles.delete_profile(name)
        return {"ok": True}
    except KeyError as e:
        return JSONResponse(status_code=404, content={"detail": str(e.args[0]) if e.args else str(e)})


@app.post("/admin/api/profiles/switch")
async def admin_switch_profile(request: Request):
    body, err = await parse_json_body(request)
    if err:
        return err
    name = body.get("name", "")
    try:
        result = profiles.switch_profile(name)
        if isinstance(result, dict) and "api_key" in result:
            result["api_key"] = mask_api_key(result["api_key"])
        return {"ok": True, "profile": result, "message": "Profile switched. Changes take effect on next request."}
    except KeyError as e:
        return JSONResponse(status_code=404, content={"detail": str(e.args[0]) if e.args else str(e)})


# ── Admin API: Claude Desktop sync ──────────────────────


@app.get("/admin/api/desktop/status")
async def admin_desktop_status():
    try:
        return desktop.get_status()
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": "Status check failed: {}".format(str(e))})


@app.post("/admin/api/desktop/sync")
async def admin_desktop_sync():
    if not desktop.is_installed():
        return JSONResponse(status_code=400, content={"detail": "Claude Desktop not installed"})
    active = profiles.get_active_profile()
    if not active:
        return JSONResponse(status_code=400, content={"detail": "No active profile"})
    try:
        models = [
            {"id": m.get("id", ""), "display_name": m.get("display_name") or m.get("id", "")}
            for m in active.get("models", [])
            if isinstance(m, dict) and m.get("id")
        ]
        result = desktop.sync_from_gateway(models, "local-gateway")
        return {"ok": True, "result": result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": "Sync failed: {}".format(str(e))})


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
    try:
        return desktop.apply_and_restart()
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": "Apply failed: {}".format(str(e))})


@app.post("/admin/api/desktop/discard")
async def admin_desktop_discard():
    try:
        desktop.discard_pending()
        return {"ok": True}
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": "Discard failed: {}".format(str(e))})
