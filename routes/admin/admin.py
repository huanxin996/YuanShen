from fastapi import APIRouter, Request, Form, FastAPI
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from methods.routes_manner import route_manager
from methods.globalvar import GlobalVars
from loguru import logger as log
import time, datetime, platform, os, psutil
import importlib.metadata

admin_router = APIRouter(prefix="/admin", tags=["admin"])

def get_system_info():
    """获取系统相关信息"""
    try:
        os_info = f"{platform.system()} {platform.release()}"
        
        is_docker = os.path.exists("/.dockerenv")
        is_kubernetes = os.path.exists("/var/run/secrets/kubernetes.io")
        
        if is_docker:
            container_env = "Docker"
        elif is_kubernetes:
            container_env = "Kubernetes"
        elif os.environ.get("CONTAINER", ""):
            container_env = os.environ.get("CONTAINER", "未知容器")
        else:
            container_env = "否"
        
        try:
            fastapi_version = importlib.metadata.version("fastapi")
        except:
            fastapi_version = "未知"
        
        mem = psutil.virtual_memory()
        mem_used = f"{mem.used / (1024 * 1024 * 1024):.2f} GB"
        mem_total = f"{mem.total / (1024 * 1024 * 1024):.2f} GB"
        mem_percent = f"{mem.percent}%"
        
        cpu_percent = f"{psutil.cpu_percent(interval=0.1)}%"
        cpu_count = psutil.cpu_count(logical=True)
        
        return {
            "os_info": os_info,
            "container_env": container_env,
            "fastapi_version": fastapi_version,
            "mem_used": mem_used,
            "mem_total": mem_total,
            "mem_percent": mem_percent,
            "cpu_percent": cpu_percent,
            "cpu_count": cpu_count
        }
    except Exception as e:
        log.error(f"获取系统信息失败: {str(e)}")
        return {
            "os_info": "获取失败",
            "container_env": "获取失败",
            "fastapi_version": "获取失败",
            "mem_used": "获取失败",
            "mem_total": "获取失败",
            "mem_percent": "0%",
            "cpu_percent": "0%",
            "cpu_count": 0
        }

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
    
    search_query = request.query_params.get("search", "")
    
    if not mw:
        return templates.TemplateResponse("admin_index.html", {
            "request": request, 
            "route_list": [], 
            "current_page": "routes",
            "search_query": search_query
        })
    
    routes = [route.path for route in app.routes if hasattr(route, "path") and route.path.startswith("/")]
    disabled = mw.disabled_routes
    route_list = []
    
    api_stats = {}
    total_calls = 0
    
    if GlobalVars.table_exists("api_stats"):
        all_vars = GlobalVars.get_all_from_table("api_stats")
        for key, value in all_vars.items():
            if key.startswith("api_count:"):
                api_path = key.replace("api_count:", "")
                api_stats[api_path] = value
                total_calls += value
        log.debug(f"从api_stats表加载了{len(api_stats)}条API统计数据")
    else:
        log.warning("api_stats表不存在，无法加载API统计数据")
    
    top_apis = sorted(api_stats.items(), key=lambda x: x[1], reverse=True)[:3]
    
    api_count = len([r for r in routes if not r.startswith("/admin") and not r.startswith("/static") and not r.startswith("/favicon.ico")])
    
    for path in sorted(routes):
        if path.startswith("/admin") or path.startswith("/static") or path.startswith("/favicon.ico"):
            continue
            
        if search_query and search_query.lower() not in path.lower():
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
        "top_apis": top_apis,
        "current_page": "routes",
        "search_query": search_query
    })

@admin_router.get("/stats")
async def admin_stats(request: Request):
    """API统计数据页面路由"""
    app = request.app
    mw = route_manager.get_protection_middleware(app)
    if not mw:
        return templates.TemplateResponse("admin_stats.html", {
            "request": request, 
            "api_stats": [], 
            "current_page": "stats"
        })
    
    routes = [route.path for route in app.routes if hasattr(route, "path") and route.path.startswith("/")]
    disabled_routes = mw.disabled_routes
    
    api_count = len([r for r in routes if not r.startswith("/admin") and not r.startswith("/static") and not r.startswith("/favicon.ico")])
    disabled_count = len([r for r in disabled_routes if not r.startswith("/admin") and not r.startswith("/static")])
    
    api_stats = {}
    total_calls = 0
    
    if GlobalVars.table_exists("api_stats"):
        all_vars = GlobalVars.get_all_from_table("api_stats")
        for key, value in all_vars.items():
            if key.startswith("api_count:"):
                api_path = key.replace("api_count:", "")
                if not api_path.startswith("/admin") and not api_path.startswith("/static") and not api_path.startswith("/favicon.ico"):
                    api_stats[api_path] = value
                    total_calls += value
        log.debug(f"从api_stats表加载了{len(api_stats)}条API统计数据")
    else:
        log.warning("api_stats表不存在，无法加载API统计数据")
    
    sorted_api_stats = []
    for rank, (path, count) in enumerate(sorted(api_stats.items(), key=lambda x: x[1], reverse=True)):
        sorted_api_stats.append({
            "rank": rank + 1,
            "path": path,
            "count": count,
            "percent": (count / total_calls * 100) if total_calls > 0 else 0,
            "status": "禁用" if path in disabled_routes else "启用",
            "status_class": "disabled" if path in disabled_routes else "enabled"
        })
    
    api_names = []
    pie_data = []
    other_count = 0
    
    raw_sorted = sorted(api_stats.items(), key=lambda x: x[1], reverse=True)
    
    for i, (path, count) in enumerate(raw_sorted):
        if i < 7:
            api_names.append(path)
            pie_data.append({"name": path, "value": count})
        else:
            other_count += count
    
    if other_count > 0 and raw_sorted:
        api_names.append("其他")
        pie_data.append({"name": "其他", "value": other_count})
    
    time_labels = []
    trend_data = []
    today = datetime.datetime.now()
    
    total_daily_stats = {}
    if GlobalVars.table_exists("api_stats"):
        total_daily_stats = GlobalVars.get_from_table("api_stats", "api_total_daily_stats", {})
    
    for i in range(7, 0, -1):
        day = today - datetime.timedelta(days=i-1)
        day_str = day.strftime("%Y-%m-%d")
        time_labels.append(day.strftime("%m-%d"))
        
        daily_count = total_daily_stats.get(day_str, 0)
        trend_data.append(daily_count)
    
    # 获取服务器启动时间
    start_time = GlobalVars.get("server_start_time", time.time())
    
    uptime_seconds = int(time.time() - start_time)
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if days > 0:
        uptime = f"{days}天{hours}小时"
    elif hours > 0:
        uptime = f"{hours}小时{minutes}分"
    else:
        uptime = f"{minutes}分{seconds}秒"
    
    system_info = get_system_info()
    
    return templates.TemplateResponse("admin_stats.html", {
        "request": request,
        "api_count": api_count,
        "total_calls": total_calls,
        "disabled_count": disabled_count,
        "disabled_routes": disabled_routes,
        "api_stats": sorted_api_stats,
        "api_names": api_names,
        "pie_data": pie_data,
        "time_labels": time_labels,
        "trend_data": trend_data,
        "uptime": uptime,
        "current_page": "stats",
        "system_info": system_info
    })

@admin_router.get("/settings")
async def admin_settings(request: Request):
    """系统设置页面路由"""
    return templates.TemplateResponse("admin_settings.html", {
        "request": request, 
        "current_page": "settings"
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