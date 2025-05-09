import os, importlib, re
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from methods.globalvar import GlobalVars
from typing import Dict, Set, List, Tuple, Pattern, Optional
from loguru import logger as log
from config import project_root

route_protection_middleware_instance = None

class RouteProtectionMiddleware(BaseHTTPMiddleware):
    """只允许访问已注册的路由，拒绝访问未注册的路径"""
    def __init__(self, app: FastAPI = None):
        super().__init__(app)
        self.allowed_paths: Set[str] = set()
        self.disabled_routes: Set[str] = set()
        self.pattern_paths: List[Tuple[Pattern, str]] = []
        self.default_paths: List[str] = ["/favicon.ico"]
        log.info(f"路由保护中间件已创建，默认允许 {len(self.default_paths)} 个系统路径")

    def disable_route(self, path: str):
        self.disabled_routes.add(path)
        log.info(f"已禁用路由: {path}")

    def enable_route(self, path: str):
        if path in self.disabled_routes:
            self.disabled_routes.remove(path)
            log.info(f"已启用路由: {path}")

    def is_route_disabled(self, path: str) -> bool:
        return path in self.disabled_routes

    def update_allowed_paths(self, app: FastAPI):
        """更新允许访问的路径列表，只保留实际存在的静态资源文件路径"""
        self.allowed_paths = set()
        self.pattern_paths = []
        self.default_paths = ["/favicon.ico"]
        self.allowed_paths.update(self.default_paths)
        
        static_dirs = {}
        base_static_paths = set()

        for route in app.routes:
            if getattr(route, "app", None).__class__.__name__ == "StaticFiles":
                path = route.path
                directory = getattr(route.app, "directory", None)
                if directory:
                    static_dirs[path] = directory
                    base_static_paths.add(path)
                self.allowed_paths.add(path)
                
            if hasattr(route, "path"):
                if "{" in route.path:
                    pattern = re.escape(route.path)
                    pattern = re.sub(r'\\\{[^}]*\\\}', r'([^/]+)', pattern)
                    self.pattern_paths.append((re.compile(f"^{pattern}$"), route.path))
                elif not getattr(route, "app", None).__class__.__name__ == "StaticFiles":
                    self.allowed_paths.add(route.path)
        
        for web_path, directory in static_dirs.items():
            if os.path.exists(directory):
                base_path = Path(directory)
                for root, dirs, files in os.walk(base_path):
                    rel_path = os.path.relpath(root, base_path)
                    for file in files:
                        if rel_path == ".":
                            file_web_path = f"{web_path}/{file}"
                        else:
                            file_web_path = f"{web_path}/{rel_path.replace(os.sep, '/')}/{file}"
                        
                        file_web_path = file_web_path.replace("//", "/")
                        self.allowed_paths.add(file_web_path)
                        
                        # 处理替代路径（如 /static/css/admin.css 对应 /admin/static/css/admin.css）
                        """
                        parts = web_path.strip("/").split("/")
                        if len(parts) > 1:
                            alt_base_path = "/" + parts[-1]
                            alt_file_path = file_web_path.replace(web_path, alt_base_path)
                            self.allowed_paths.add(alt_file_path)
                        """
                
                log.debug(f"已添加静态目录 {directory} 下的所有文件路径到允许列表")
        
        for path in base_static_paths:
            if path in self.allowed_paths:
                self.allowed_paths.remove(path)
                log.debug(f"从允许列表移除静态资源基础路径: {path}")
        
        log.info(f"路由保护已更新: 允许访问 {len(self.allowed_paths)} 个固定路径和 {len(self.pattern_paths)} 个参数路径")
        log.debug(f"允许访问的路径: {self.allowed_paths}")
        log.debug(f"参数化路径: {self.pattern_paths}")

    async def dispatch(self, request: Request, call_next):
        """处理请求，验证路径是否允许访问，并记录API访问次数"""
        if not self.allowed_paths:
            self.update_allowed_paths(request.app)
        path = request.url.path
        
        if self.is_route_disabled(path):
            log.warning(f"访问被禁用的路由: {path}")
            return PlainTextResponse("该API已被禁用", status_code=403)
        
        if path in self.allowed_paths:
            response = await call_next(request)
            
            if (not path.startswith("/admin") and 
                not path.startswith("/static") and 
                not path.endswith((".css", ".js", ".ico", ".png", ".jpg", ".jpeg", ".gif"))):
                
                api_count_key = f"api_count:{path}"
                current_count = GlobalVars.get(api_count_key, 0)
                GlobalVars.set(api_count_key, current_count + 1)
                log.debug(f"API访问计数: {path} -> {current_count + 1}")
            
            return response
        
        parts = path.split('/')
        if len(parts) > 2:
            base_path = f"/{parts[1]}"
            if f"{base_path}/{{path:path}}" in self.allowed_paths or f"{base_path}" in self.allowed_paths:
                log.debug(f"允许访问静态资源子路径: {path}")
                return await call_next(request)
        
        for pattern, original_path in self.pattern_paths:
            if pattern.match(path):
                response = await call_next(request)
                
                if (not original_path.startswith("/admin") and 
                    not original_path.startswith("/static")):
                    
                    api_count_key = f"api_count:{original_path}"
                    current_count = GlobalVars.get(api_count_key, 0)
                    GlobalVars.set(api_count_key, current_count + 1)
                    log.debug(f"参数化API访问计数: {original_path} -> {current_count + 1}")
                
                return response
        
        log.warning(f"拒绝访问未注册路径: {path} (方法: {request.method})")
        return PlainTextResponse(
            "你瞅啥，不要乱访问好不好？",
            status_code=403
        )



class RouteManager:
    """
    通用路由管理器，用于自动寻找和注册路由
    """
    def __init__(self):
        self.routers: Dict[str, APIRouter] = {}
        self.routes_models_path: Path = project_root / 'static'
        self.route_modules = {}
        self.registered_routes: Dict[str, Set[str]] = {}
        self.total_routes = 0
        self.preserved_routes: List[str] = ["/favicon.ico"]
        self._protection_updated = False
        self._middleware_instance: Optional[RouteProtectionMiddleware] = None

    def discover_routes(self, routes_dir: str = "routes") -> None:
        """
        自动发现指定目录下的所有路由模块
        """
        log.info(f"开始寻找路由文件，路径: {routes_dir}")
        base_path = os.path.join(os.getcwd(), routes_dir)
        
        if not os.path.exists(base_path):
            log.warning(f"路由目录不存在: {base_path}")
            return

        self.route_modules.clear()
        
        for root, dirs, files in os.walk(base_path):
            if "__pycache__" in root:
                continue
            
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, os.getcwd())
                    module_path = rel_path.replace(os.sep, ".")[:-3]
                    
                    try:
                        log.info(f"尝试导入路由模块: {module_path}")
                        module = importlib.import_module(module_path)
                        
                        if hasattr(module, "register_routes"):
                            module_name = file[:-3]
                            self.route_modules[module_name] = module
                            log.info(f"发现路由模块: {module_name}")
                        else:
                            log.warning(f"模块 {module_path} 没有 register_routes 函数")
                    
                    except Exception as e:
                        log.error(f"导入模块 {module_path} 失败: {e}")

        log.info(f"路由发现完成，共找到 {len(self.route_modules)} 个路由模块")

    def clear_routes(self, app: FastAPI, preserve_defaults: bool = True) -> int:
        """移除应用中的所有现有路由"""
        if not hasattr(app, 'routes'):
            log.warning("应用没有routes属性，无法清理路由")
            return 0
            
        original_count = len(app.routes)
        
        if preserve_defaults and self.preserved_routes:
            preserved = []
            removed = []
            
            for route in app.routes:
                if hasattr(route, 'path') and route.path in self.preserved_routes:
                    preserved.append(route)
                else:
                    removed.append(route)
                    
            app.routes.clear()
            
            for route in preserved:
                app.routes.append(route)
                
            removed_count = original_count - len(preserved)
            log.info(f"已移除 {removed_count} 个路由，保留了 {len(preserved)} 个默认路由")
        else:
            removed_count = len(app.routes)
            app.routes.clear()
            log.info(f"已移除所有 {removed_count} 个路由，包括默认路由")
            
        self._protection_updated = False
        return removed_count

    def register_all_routes(self, app: FastAPI, prefix: str = "", clear_existing: bool = True) -> None:
        """注册所有发现的路由到 FastAPI 应用"""
        log.info(f"开始注册所有路由，前缀: {prefix}")
        
        if clear_existing:
            self.clear_routes(app)
        
        routes_before = self._count_routes(app)
        
        all_registered_paths = set()
        
        for module_name, module in self.route_modules.items():
            try:
                log.info(f"注册模块 {module_name} 的路由")
                module_routes_before = self._count_routes(app)
                
                module.register_routes(app)
                
                module_routes_after = self._count_routes(app)
                routes_added = module_routes_after - module_routes_before
                
                new_paths = set([r.path for r in app.routes[-routes_added:]])
                self.registered_routes[module_name] = new_paths
                all_registered_paths.update(new_paths)
                
                log.info(f"模块 {module_name} 添加了 {routes_added} 个路由")
            except Exception as e:
                log.error(f"注册模块 {module_name} 的路由失败: {e}")
        
        routes_after = self._count_routes(app)
        self.total_routes = routes_after
        
        log.info(f"所有路由注册完成，共添加 {routes_after - routes_before} 个路由，当前总路由数: {self.total_routes}")
        
        self.print_registered_routes(app)
        
        log.info("所有路由已注册，开始更新路由保护...")
        self.add_route_protection(app)
        self.update_route_protection(app)

    def register_route_module(self, app: FastAPI, module_name: str, prefix: str = "", clear_before: bool = False) -> bool:
        """注册单个路由模块"""
        if module_name in self.route_modules:
            try:
                if clear_before:
                    self.clear_routes(app, False)
                    
                log.info(f"注册模块 {module_name} 的路由")
                
                routes_before = self._count_routes(app)
                
                self.route_modules[module_name].register_routes(app)
                
                routes_after = self._count_routes(app)
                routes_added = routes_after - routes_before
                self.registered_routes[module_name] = set([
                    r.path for r in app.routes[-routes_added:]
                ])
                
                self.total_routes = routes_after
                
                log.info(f"模块 {module_name} 添加了 {routes_added} 个路由，当前总路由数: {self.total_routes}")
                
                self.update_route_protection(app)
                self._protection_updated = True
                
                return True
            except Exception as e:
                log.error(f"注册模块 {module_name} 的路由失败: {e}")
                return False
        else:
            log.error(f"找不到路由模块: {module_name}")
            return False
    
    def register_static_route(self, app: FastAPI, path: str, directory: str, name: str = "static", auto_register_alternate_path: bool = False):
        """
        注册静态资源路由
        
        参数:
            app: FastAPI应用
            path: 静态资源路径，如 "/admin/static"
            directory: 本地目录路径
            name: 路由名称
            auto_register_alternate_path: 是否自动注册替代路径 (默认为False)
        """
        app.mount(path, StaticFiles(directory=directory), name=name)
        
        if auto_register_alternate_path:
            parts = path.strip("/").split("/")
            if len(parts) > 1:
                alternate_path = "/" + parts[-1]
                try:
                    if not any(route.path == alternate_path for route in app.routes if hasattr(route, "path")):
                        app.mount(alternate_path, StaticFiles(directory=directory), name=f"{name}_alt")
                        log.info(f"自动注册替代静态资源路径: {alternate_path} -> {directory}")
                except Exception as e:
                    log.warning(f"注册替代路径 {alternate_path} 失败: {e}")
        
        mw = self.get_protection_middleware(app)
        if mw:
            mw.update_allowed_paths(app)

    def ensure_static_routes_allowed(self, app: FastAPI):
        """
        确保所有静态资源路由都被允许访问，但只允许原始路径和其参数化版本
        """
        mw = self.get_protection_middleware(app)
        if not mw:
            return
            
        for route in app.routes:
            if getattr(route, "app", None).__class__.__name__ == "StaticFiles":
                path = route.path
                if path not in mw.allowed_paths:
                    mw.allowed_paths.add(path)
                    log.info(f"允许访问静态资源路径: {path}")
                    
                param_path = path.rstrip("/") + "/{path:path}"
                if param_path not in mw.allowed_paths:
                    mw.allowed_paths.add(param_path)
                    log.info(f"允许访问参数化静态资源路径: {param_path}")

    def get_protection_middleware(self, app: FastAPI) -> Optional[RouteProtectionMiddleware]:
        global route_protection_middleware_instance
        if route_protection_middleware_instance:
            return route_protection_middleware_instance
        stack = getattr(app, "middleware_stack", None)
        while stack:
            if isinstance(getattr(stack, "app", None), RouteProtectionMiddleware):
                route_protection_middleware_instance = stack.app
                return stack.app
            stack = getattr(stack, "app", None)
        return None

    def _find_protection_middleware(self, stack):
        """递归查找 RouteProtectionMiddleware 实例"""
        while stack:
            if isinstance(getattr(stack, "app", None), RouteProtectionMiddleware):
                return stack.app
            stack = getattr(stack, "app", None)
        return None

    def add_route_protection(self, app: FastAPI) -> None:
        """为应用添加路由保护中间件，并在启动后自动刷新允许路径"""
        log.info("正在添加路由保护中间件...")

        app.add_middleware(RouteProtectionMiddleware)

        @asynccontextmanager
        async def protection_lifespan(app: FastAPI):
            log.info("应用启动时检查路由保护状态...")
            protection_middleware = None
            if hasattr(app, 'middleware_stack') and app.middleware_stack:
                protection_middleware = self._find_protection_middleware(app.middleware_stack)
            if not protection_middleware and hasattr(app, 'user_middleware'):
                for mw_config in app.user_middleware:
                    if getattr(mw_config, 'cls', None) == RouteProtectionMiddleware:
                        log.info("在用户中间件配置中找到路由保护中间件")
                        break
            if protection_middleware:
                protection_middleware.update_allowed_paths(app)
                self._protection_updated = True
                log.info("已在应用启动时成功更新路由保护中间件")
            else:
                log.warning("应用启动时未找到路由保护中间件实例，保护配置可能不会生效")
            yield
            log.info("应用关闭时的路由保护清理...")

        original_lifespan = getattr(app.router, "lifespan_context", None)
        if original_lifespan:
            @asynccontextmanager
            async def combined_lifespan(app: FastAPI):
                async with protection_lifespan(app):
                    async with original_lifespan(app):
                        yield
            app.router.lifespan_context = combined_lifespan
        else:
            app.router.lifespan_context = protection_lifespan
        log.info("已添加路由保护中间件")

    def update_route_protection(self, app: FastAPI) -> None:
        mw = self.get_protection_middleware(app)
        if mw:
            mw.update_allowed_paths(app)
            log.info("动态更新路由保护允许路径成功")
        else:
            log.warning("未找到路由保护中间件实例，无法动态更新，将在应用启动后自动刷新")

    def disable_api(self, app: FastAPI, path: str):
        mw = self.get_protection_middleware(app)
        if mw:
            mw.disable_route(path)
        else:
            log.warning("未找到路由保护中间件实例，无法禁用API")

    def enable_api(self, app: FastAPI, path: str):
        mw = self.get_protection_middleware(app)
        if mw:
            mw.enable_route(path)
        else:
            log.warning("未找到路由保护中间件实例，无法启用API")

    def get_total_routes(self) -> int:
        """获取当前注册的路由总数"""
        return self.total_routes
    
    def get_module_routes(self, module_name: str) -> Set[str]:
        """获取指定模块的所有路由"""
        return self.registered_routes.get(module_name, set())
    
    def print_registered_routes(self, app: FastAPI) -> None:
        """打印所有已注册路由的信息"""
        log.info("=== 已注册路由列表 ===")
        for route in app.routes:
            if hasattr(route, "methods"):
                methods = ", ".join(route.methods)
                log.info(f"{methods:12} {route.path}")
        log.info(f"共 {self._count_routes(app)} 个路由")
    
    def _count_routes(self, app: FastAPI) -> int:
        """计算应用中的路由数量"""
        return len(app.routes)

route_manager = RouteManager()