import logging

from backend.controller.auth_controller import register_auth_routes
from backend.controller.chat_controller import register_chat_routes
from backend.controller.file_controller import register_file_routes
from backend.controller.health_controller import register_health_routes
from backend.controller.share_controller import register_share_routes
from backend.controller.helpers import init_helpers


def register_controllers(app, logger=None):
    controller_logger = logger or logging.getLogger(__name__)
    init_helpers(controller_logger)

    register_auth_routes(app, controller_logger)
    register_share_routes(app, controller_logger)
    register_file_routes(app, controller_logger)
    register_chat_routes(app, controller_logger)
    register_health_routes(app, controller_logger)
