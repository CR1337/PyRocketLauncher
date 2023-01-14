from flask import Flask
from flask_cors import CORS

from backend.config import Config
from backend.endpoints.device import device_bp
from backend.endpoints.master import master_bp
from backend.endpoints.shared import shared_bp
from backend.instance import Instance
from backend.led_controller import LedController
from backend.logger import logger
from backend.system import System


def run():
    Instance.initialize()

    app = Flask(__name__)

    CORS(app)

    app.static_folder = f"{app.root_path}/frontend"

    app.register_blueprint(shared_bp)
    if Instance.is_master():
        logger.info("Initializing in master mode")
        app.register_blueprint(master_bp)
    else:
        logger.info("Initializing in device mode")
        app.register_blueprint(device_bp)

    debug_str = ' in debug mode' if Config.get_value('debug') else ''
    logger.info(
        f"Running app{debug_str}..."
    )
    try:
        System.run_ntp_service()
        led_controller = LedController()
        led_controller.load_preset('idle')
        app.run(
            debug=Config.get_value('debug'),
            port=Instance.get_server_port(),
            host="0.0.0.0",
            threaded=True,
            use_reloader=Config.get_value('debug')
        )
    except Exception:
        logger.exception("Exception running app!")
    finally:
        led_controller.off()


if __name__ == "__main__":
    run()
