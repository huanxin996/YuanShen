from fastapi import APIRouter, Request, Form, FastAPI
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from methods.routes_manner import route_manager
from methods.globalvar import GlobalVars
from loguru import logger as log

admin_router = APIRouter(prefix="/admin", tags=["admin"])

def register_routes(app: FastAPI):
    log.info(f"注册admin路由，前缀：{admin_router.prefix}")
    app.include_router(admin_router)
    route_manager.register_static_route(app, "/admin/static", "routes/admin/static", name="admin_static")
    route_manager.ensure_static_routes_allowed(app)

templates = Jinja2Templates(directory="routes/admin/templates")

@admin_router.get("/manage")
async def admin_manage(request: Request):
    app = request.app
    mw = route_manager.get_protection_middleware(app)
    if not mw:
        return templates.TemplateResponse("admin_index.html", {"request": request, "route_list": []})
    
    routes = [route.path for route in app.routes if hasattr(route, "path") and route.path.startswith("/")]
    disabled = mw.disabled_routes
    route_list = []
    
    api_stats = {}
    total_calls = 0
    
    for key in GlobalVars.get_all_keys():
        if key.startswith("api_count:"):
            api_path = key.replace("api_count:", "")
            count = GlobalVars.get(key, 0)
            api_stats[api_path] = count
            total_calls += count
    
    top_apis = sorted(api_stats.items(), key=lambda x: x[1], reverse=True)[:3]
    
    api_count = len([r for r in routes if not r.startswith("/admin") and not r.startswith("/static")])
    
    for path in sorted(routes):
        if path.startswith("/admin"):
            continue
        status = "禁用" if path in disabled else "启用"
        action = "enable" if path in disabled else "disable"
        btn_class = "enable" if action == "enable" else "disable"
        btn_text = "启用" if action == "enable" else "禁用"
        access_count = api_stats.get(path, 0)
        route_list.append((path, status, action, btn_class, btn_text, access_count))
    
    return templates.TemplateResponse("admin_index.html", {
        "request": request, 
        "route_list": route_list,
        "api_count": api_count,
        "total_calls": total_calls,
        "top_apis": top_apis
    })

@admin_router.post("/action")
async def admin_action(request: Request, action: str = Form(...)):
    app = request.app
    act, path = action.split(":", 1)
    if act == "disable":
        route_manager.disable_api(app, path)
    elif act == "enable":
        route_manager.enable_api(app, path)
    
    return RedirectResponse(url="/admin/manage", status_code=303)