

class Logger(object):
    """
    Logging interface
    """

    app_logger = None

    def info(info_text, detail_text="", user=None, stack=False):
        if Logger.app_logger:
            Logger.app_logger.info(info_text, detail_text, user, stack)

    def debug(info_text, detail_text="", user=None, stack=False):
        if Logger.app_logger:
            Logger.app_logger.debug(info_text, detail_text, user, stack)

    def warning(info_text, detail_text="", user=None, stack=False):
        if Logger.app_logger:
            Logger.app_logger.warning(info_text, detail_text, user, stack)

    def error(info_text, detail_text="", user=None, stack=False):
        if Logger.app_logger:
            Logger.app_logger.error(info_text, detail_text, user, stack)

    def notify(info_text, detail_text="", user=None):
        if Logger.app_logger:
            Logger.app_logger.notify(info_text, detail_text, user, stack)

    def exc(exception_object, info_text=None, user=None):
        if Logger.app_logger:
            Logger.app_logger.exc(exception_object, info_text)
