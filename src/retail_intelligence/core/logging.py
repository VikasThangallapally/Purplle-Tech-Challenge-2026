import logging

from pythonjsonlogger.jsonlogger import JsonFormatter

from retail_intelligence.core.config import settings
from retail_intelligence.core.context import request_id_var


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def configure_logging() -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    handler = logging.StreamHandler()
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(JsonFormatter("%(asctime)s %(levelname)s %(name)s %(request_id)s %(message)s"))
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.log_level)
