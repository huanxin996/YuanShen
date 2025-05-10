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
        # 获取系统类型
        os_info = f"{platform.system()} {platform.release()}"
        
        # 检查是否在容器环境中运行
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
        
        # 获取FastAPI版本
        try:
            fastapi_version = importlib.metadata.version("fastapi")
        except:
            fastapi_version = "未知"
        
        # 获取系统内存使用情况
        mem = psutil.virtual_memory()
        mem_total = mem.total / (1024 * 1024 * 1024)  # GB
        mem_used = mem.used / (1024 * 1024 * 1024)  # GB
        mem_available = mem.available / (1024 * 1024 * 1024)  # GB
        
        mem_total_str = f"{mem_total:.2f} GB"
        mem_used_str = f"{mem_used:.2f} GB"
        mem_available_str = f"{mem_available:.2f} GB"
        
        system_mem_percent = mem.percent
        
        # 获取当前进程内存使用情况
        process = psutil.Process(os.getpid())
        process_mem = process.memory_info().rss / (1024 * 1024 * 1024)  # GB
        process_mem_str = f"{process_mem:.2f} GB"
        
        # 计算当前进程占系统内存的百分比
        process_percent = (process_mem / mem_total) * 100
        process_percent_str = f"{process_percent:.1f}%"
        
        # 获取系统CPU使用率
        system_cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count(logical=True)
        
        # 获取当前进程CPU使用率
        process_cpu_percent = process.cpu_percent(interval=0.1) / cpu_count
        
        # 获取服务器启动时间
        start_time = GlobalVars.get("server_start_time", time.time())
        server_start_timestamp = int(start_time)
        
        return {
            "os_info": os_info,
            "container_env": container_env,
            "fastapi_version": fastapi_version,
            "mem_total": mem_total_str,
            "mem_used": mem_used_str, 
            "mem_available": mem_available_str,
            "system_mem_percent": system_mem_percent,
            "process_mem": process_mem_str,
            "process_percent": process_percent_str,
            "process_percent_raw": process_percent,
            "system_cpu_percent": system_cpu_percent,
            "system_cpu_percent_str": f"{system_cpu_percent}%",
            "cpu_count": cpu_count,
            "process_cpu_percent": process_cpu_percent,
            "process_cpu_percent_str": f"{process_cpu_percent:.1f}%",
            "server_start_timestamp": server_start_timestamp
        }
    except Exception as e:
        log.error(f"获取系统信息失败: {str(e)}")
        return {
            "os_info": "获取失败",
            "container_env": "获取失败",
            "fastapi_version": "获取失败",
            "mem_total": "未知",
            "mem_used": "未知",
            "mem_available": "未知",
            "system_mem_percent": 0,
            "process_mem": "未知",
            "process_percent": "0%",
            "process_percent_raw": 0,
            "system_cpu_percent": 0,
            "system_cpu_percent_str": "0%",
            "cpu_count": 0,
            "process_cpu_percent": 0,
            "process_cpu_percent_str": "0%",
            "server_start_timestamp": 0
        }

def register_routes(app: FastAPI):
    log.info(f"注册admin路由，前缀：{admin_router.prefix}")
    app.include_router(admin_router)
    route_manager.register_static_route(app, "/admin/static", "routes/admin/static", name="admin_static")
    route_manager.ensure_static_routes_allowed(app)

templates = Jinja2Templates(directory="routes/admin/templates")

@admin_router.get("/manage")
async def admin_manage(request: Request):
    """路由管理页面，专注于路由列表和状态管理"""
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
    
    if GlobalVars.table_exists("api_stats"):
        all_vars = GlobalVars.get_all_from_table("api_stats")
        for key, value in all_vars.items():
            if key.startswith("api_count:"):
                api_path = key.replace("api_count:", "")
                api_stats[api_path] = value
    else:
        log.warning("api_stats表不存在，无法加载API统计数据")
    
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
        "current_page": "routes",
        "search_query": search_query
    })

@admin_router.get("/stats")
async def admin_stats(request: Request):
    """API统计数据页面路由，包含所有统计信息和系统监控"""
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
    else:
        log.warning("api_stats表不存在，无法加载API统计数据")
    
    # 为热门API排行准备数据
    top_apis = sorted(api_stats.items(), key=lambda x: x[1], reverse=True)[:3]
    
    # 为完整API统计表格准备数据
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
    
    # 为饼图准备数据
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
    
    # 为趋势图准备数据
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
    
    # 获取系统信息
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
        "top_apis": top_apis,
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