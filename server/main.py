#!/usr/bin/env python3

from configparser import ConfigParser
from common.server import Server
from common.interrupts_handler import set_sigterm_handler, TerminationSignal
import logging
import os


def initialize_config():
    """Parse env variables or config file to find program config params

    Function that search and parse program configuration parameters in the
    program environment variables first and the in a config file.
    If at least one of the config parameters is not found a KeyError exception
    is thrown. If a parameter could not be parsed, a ValueError is thrown.
    If parsing succeeded, the function returns a ConfigParser object
    with config parameters
    """

    config = ConfigParser(os.environ)
    # If config.ini does not exists original config object is not modified
    config.read("config.ini")

    config_params = {}
    try:
        config_params["port"] = int(config["DEFAULT"]["server_port"])
        config_params["listen_backlog"] = int(
            config["DEFAULT"]["server_listen_backlog"]
        )
        config_params["logging_level"] = config["DEFAULT"]["logging_level"]
        config_params["timeout"] = int(config["DEFAULT"]["timeout"])
        config_params["thread_pool_size"] = int(config["DEFAULT"]["thread_pool_size"])
        config_params["agencies_count"] = int(config["DEFAULT"]["agencies_count"])
    except KeyError as e:
        raise KeyError("Key was not found. Error: {} .Aborting server".format(e))
    except ValueError as e:
        raise ValueError(
            "Key could not be parsed. Error: {}. Aborting server".format(e)
        )

    return config_params


def main():
    config_params = initialize_config()
    logging_level = config_params["logging_level"]
    port = config_params["port"]
    listen_backlog = config_params["listen_backlog"]

    initialize_log(logging_level)

    # Log config parameters at the beginning of the program to verify the configuration
    # of the component
    logging.debug(
        f"action: config | result: success | port: {port} | "
        f"listen_backlog: {listen_backlog} | logging_level: {logging_level}"
    )

    # Initialize server and start server loop
    server = Server(
        config_params["port"],
        config_params["listen_backlog"],
        config_params["timeout"],
        config_params["thread_pool_size"],
        config_params["agencies_count"],
    )
    set_sigterm_handler()
    try:
        server.run()
    except (KeyboardInterrupt, TerminationSignal) as e:
        logging.info(f"[ServerThread] Received interrupt: {e}")


def initialize_log(logging_level):
    """
    Python custom logging initialization

    Current timestamp is added to be able to identify in docker
    compose logs the date when the log has arrived
    """
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=logging_level,
        datefmt="%Y-%m-%d %H:%M:%S",
    )


if __name__ == "__main__":
    main()
