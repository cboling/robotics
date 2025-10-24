# ------------------------------------------------------------------------ #
#      o-o      o                o                                         #
#     /         |                |                                         #
#    O     o  o O-o  o-o o-o     |  oo o--o o-o o-o                        #
#     \    |  | |  | |-' |   \   o | | |  |  /   /                         #
#      o-o o--O o-o  o-o o    o-o  o-o-o--O o-o o-o                        #
#             |                           |                                #
#          o--o                        o--o                                #
#                        o--o      o         o                             #
#                        |   |     |         |  o                          #
#                        O-Oo  o-o O-o  o-o -o-    o-o o-o                 #
#                        |  \  | | |  | | |  |  | |     \                  #
#                        o   o o-o o-o  o-o  o  |  o-o o-o                 #
#                                                                          #
#    Jemison High School - Huntsville Alabama                              #
# ------------------------------------------------------------------------ #

import logging


def init_logging() -> logging.Logger:
    #    - level: Sets the minimum severity level for messages to be processed.
    #             Messages below this level will be ignored.
    #    - format: Defines the layout of the log messages.
    #              %(asctime)s: Timestamp of the log record.
    #              %(levelname)s: Textual logging level (e.g., INFO, DEBUG).
    #              %(name)s: Name of the logger (e.g., __main__ if not specified).
    #              %(message)s: The actual log message.
    #    - handlers: A list of handlers to which the root logger will send messages.
    #                Here, we add a FileHandler to write to 'app.log' and a StreamHandler
    #                to output to the console.

    logging.Formatter(
        fmt='%(asctime)s.%(msecs)03d',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logging.basicConfig(
        level=logging.INFO,
        # format='%(asctime)s.%(msecs)03d %(levelname)-8s - %(name)-12s %(message)s',
        format='%(asctime)s %(levelname)-6s - %(name)-12s %(message)s',
        handlers=[
            # logging.FileHandler("cyberjagzz-robot.log"),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger("CyberJagzz Robot")
    #
    # # 1. Get a logger instance for your module
    # #    Using __name__ ensures that the logger is named after the current module,
    # #    which is helpful for identifying the source of log messages in larger applications.
    # logger.setLevel(logging.DEBUG)  # Set the minimum logging level for the logger
    #
    # # Define the format for log messages.
    # formatter = logging.Formatter('%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s')
    #
    # # Console Handler (StreamHandler)
    # console_handler = logging.StreamHandler()
    # console_handler.setLevel(logging.INFO)  # Only INFO and higher messages to console
    # console_handler.setFormatter(formatter)
    # logger.addHandler(console_handler)
    #
    # # Rotating File Handler
    # # log_file.log will be the current log file.
    # # maxBytes=1024 (1KB) for demonstration; use a larger value in production.
    # # backupCount=3 means it will keep log_file.log.1, log_file.log.2, log_file.log.3
    # file_handler = RotatingFileHandler(
    #     'cyberjagzz-robot.log',
    #     maxBytes=128 *1024,  # Rotate after 128k
    #     backupCount=3  # Keep 3 backup files
    # )
    # file_handler.setLevel(logging.DEBUG)  # Log all messages to the file
    # file_handler.setFormatter(formatter)
    # logger.addHandler(file_handler)

    return logger
