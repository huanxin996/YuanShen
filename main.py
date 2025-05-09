import uvicorn, asyncio, signal,os,sys
from api.maimai50.maimaidx_music import initialize_maimai_data
from loguru import logger as log
from fastapi import FastAPI
from methods.routes_manner import route_manager
from methods.loggers import get_log_config


app = FastAPI()
server = None
should_exit = False

async def init_app():
    global app
    await initialize_maimai_data()
    route_manager.discover_routes()
    route_manager.register_all_routes(app)
    log.info("验证路由保护中间件是否生效...")
    has_protection = False
    if hasattr(app, 'user_middleware'):
        for mw_config in app.user_middleware:
            if hasattr(mw_config, 'cls') and mw_config.cls.__name__ == 'RouteProtectionMiddleware':
                log.info("路由保护中间件已添加到应用配置")
                has_protection = True
                break
        if not has_protection:
            log.warning("路由保护中间件未找到")
    else:
        log.warning("应用没有user_middleware属性，路由保护可能未生效")
    log.info(f"应用初始化完成，共注册 {len(app.routes)} 个路由")


async def shutdown(signal_type=None):
    global should_exit
    if should_exit:
        return
    should_exit = True
    if signal_type:
        log.info(f"收到信号 {signal_type.name}，准备关闭服务器...")
    else:
        log.info("准备关闭服务器...")
    if server:
        log.info("正在关闭服务器...")
        server.should_exit = True
        await server.shutdown()
    log.info("服务器已完全关闭")
    os._exit(0)

def signal_handler(sig, frame):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop.create_task(shutdown(signal.Signals(sig)))

async def run_server_async():
    """异步启动服务器"""
    global server, app

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, signal_handler)
    
    if hasattr(signal, 'SIGHUP'):
        signal.signal(signal.SIGHUP, signal_handler)
    
    # 配置日志
    custom_log_config = get_log_config()

    # 初始化应用
    await init_app()
    
    log.info(f"服务器正在启动... 运行环境: {'Linux/Ubuntu' if sys.platform.startswith('linux') else 'Windows'}")
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=9090,
        log_level="info",
        reload=False,
        log_config=custom_log_config
    )
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    except Exception as e:
        log.error(f"服务器运行出错: {e}")
    finally:
        if not should_exit:
            await shutdown()

def run_server():
    try:
        asyncio.run(run_server_async())
    except KeyboardInterrupt:
        log.info("收到键盘中断，服务器已停止")
    except Exception as e:
        log.error(f"服务器启动失败: {e}")
        os._exit(1)

if __name__ == "__main__":
    run_server()