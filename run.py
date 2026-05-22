# Deployment entry point - imports server from a^{-x}.py for gunicorn
from importlib.util import spec_from_file_location, module_from_spec

spec = spec_from_file_location("app_module", "a^{-x}.py")
app_module = module_from_spec(spec)
spec.loader.exec_module(app_module)

server = app_module.server
app = app_module.app
