
import logging
import os

import tornado.web

logger = logging.getLogger(__name__)


class Application(tornado.web.Application):

    pass


def init_handler(context):
    logger.info("'%s' app init handler", context.config.name)


def sigusr1_handler(context):
    logger.info(
        "'%s' app sigusr1 handler, pid %d",
        context.config.name, os.getpid()
    )


def sigusr2_handler(context):
    logger.info(
        "'%s' app sigusr2 handler, pid %d",
        context.config.name, os.getpid()
    )


def app_settings_handler(context):
    return {
        'cookie_secret': context.config.secret_key,
    }
