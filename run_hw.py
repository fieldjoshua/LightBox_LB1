import os
import sys
import signal
import threading
import logging

os.chdir('/home/joshuafield/LightBox2.0')
sys.path.insert(0, '/home/joshuafield/LightBox2.0')

from core.conductor import Conductor
from web.app_simple import create_app, run_server


def main():
    logging.basicConfig(level=logging.INFO)

    def _shutdown(_signum, _frame):
        os._exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    conductor = Conductor()
    if not conductor.initialize():
        raise SystemExit('Conductor init failed')

    app = create_app(conductor)

    # Start animation loop in background
    threading.Thread(target=conductor.run, daemon=True).start()

    # Start simple Flask server (SocketIO disabled in app)
    port = conductor.config.get("web.port", 8888)
    run_server(app, host='0.0.0.0', port=port, production=False)


if __name__ == '__main__':
    main()


