NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

from .cuicommander.api import register_routes
from .cuicommander.remote_access import register_remote_access

register_routes()
register_remote_access()
