from loguru import logger


logger.add('errors.log', level='DEBUG',
           format='{time} {level} {message}')
