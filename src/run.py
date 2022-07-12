import click
import os
from pathlib import Path
from . import main
import socket
import uvicorn


def find_port(port=8000):
    """Find a port not in ues starting at given port"""
    # Stolen from https://waylonwalker.com/python-find-available-port/
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("localhost", port)) == 0:
            return find_port(port=port + 1)
        else:
            return port


@click.command()
@click.option("--host", "-H", default="127.0.0.1", help="The host IP to listen on.")
@click.option(
    "--port",
    "-P",
    default="auto:8000",
    help="The port to run on. " "`auto` detects the next available port after `:n`.",
)
@click.option("--directory", "-D", default=Path.cwd(), type=Path, help="The directory to serve")
def run_server(host: str, port: str, directory: Path):
    if port.lower().startswith("auto"):
        try:
            _, start = port.split(":")
        except ValueError:
            start = 8000
        else:
            start = int(start)
        port = find_port(start)
    else:
        port = int(port)

    os.chdir(directory)
    uvicorn.run(main.app, host=host, port=port)


if __name__ == "__main__":
    run_server()
