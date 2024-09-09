import traceback

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

    def use_print_logging():
        Logger.app_logger = PrintLogger


class PrintLogger(object):
    """
    Implementation of weblogger that only prints to std out
    """

    def info(info_text, detail_text="", user=None, stack=False):
        print(info_text)
        if detail_text:
            print(detail_text)

    def debug(info_text, detail_text="", user=None, stack=False):
        print(info_text)
        if detail_text:
            print(detail_text)

    def warning(info_text, detail_text="", user=None, stack=False):
        print(info_text)
        if detail_text:
            print(detail_text)

    def error(info_text, detail_text="", user=None, stack=False):
        print(info_text)
        if detail_text:
            print(detail_text)

    def notify(info_text, detail_text="", user=None):
        print(info_text)
        if detail_text:
            print(detail_text)

    def exc(exception_object, info_text=None, user=None):
        print(str(exception_object))

        error_text = traceback.format_exc()
        print("Exception format")
        print(error_text)

        stack_lines = traceback.format_stack()
        stack_string = "".join(stack_lines)
        print("Stack:")
        print("".join(stack_lines))
