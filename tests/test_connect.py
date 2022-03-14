# -*- coding: utf-8 -*-

# stdlib imports
from server import sio, app
import sys
import os
from typing import List, Optional
import asyncio

# 3rd party imports
import pytest_asyncio
import pytest

# Web3 related
from web3.auto import w3
from eth_account.messages import encode_defunct

# App imports
from fastapi import FastAPI
import socketio
import uvicorn

# App package TODO: bad relative import
sys.path.append(os.path.join(__file__, ".."))


PORT = 8080

# Testing account
TESTING_PRIVATE_KEY = "10818f935e7f7b7317e2cde9841c29bca619b11b24bb9e3603542728d227cc26"
TESTING_ADDRESS = "0xD056bA7d32c8C83a0404940245d4a89056Dfc699"

# deactivate monitoring task in python-socketio to avoid errores during shutdown
sio.eio.start_service_task = False


class UvicornTestServer(uvicorn.Server):
    """Uvicorn test server

    Usage:
        @pytest.fixture
        async def start_stop_server():
            server = UvicornTestServer()
            await server.up()
            yield
            await server.down()
    """

    def __init__(self, app: FastAPI = app, host: str = "127.0.0.1", port: int = PORT):
        """Create a Uvicorn test server

        Args:
            app (FastAPI, optional): the FastAPI app. Defaults to app.
            host (str, optional): the host ip. Defaults to '127.0.0.1'.
            port (int, optional): the port. Defaults to PORT.
        """
        self._startup_done = asyncio.Event()
        super().__init__(config=uvicorn.Config(app, host=host, port=port))

    # Funcions for serving out testing server
    async def startup(self, sockets: Optional[List] = None) -> None:
        """Override uvicorn startup"""
        await super().startup(sockets=sockets)
        self.config.setup_event_loop()
        self._startup_done.set()

    async def up(self) -> None:
        """Start up server asynchronously"""
        self._serve_task = asyncio.create_task(self.serve())
        await self._startup_done.wait()

    async def down(self) -> None:
        """Shut down server asynchronously"""
        self.should_exit = True
        # self.force_exit = True
        await self._serve_task
        # await self.shutdown()


# !!! MUST be in every func with testing socketio server
@pytest_asyncio.fixture
async def startup_and_shutdown_server():
    """Start server as test fixture and tear down after test"""
    server = UvicornTestServer()
    await server.up()
    yield
    await server.down()


@pytest.mark.asyncio
async def test_auth(startup_and_shutdown_server):
    # Client instance
    socket_client = socketio.AsyncClient()
    # Preparing for server response
    future_session = asyncio.get_running_loop().create_future()

    @socket_client.on("session_key")
    async def session_key_getter(data):
        session_data = data["session_key"]
        # set the response of server to 'result'
        future_session.set_result(session_data)

    print("Client connected to server")
    await socket_client.connect(
        f"http://localhost:{PORT}", socketio_path="/sio/socket.io/"
    )

    # wait for the result to be set (avoid waiting forever)
    await asyncio.wait_for(future_session, timeout=0.5)

    session_key = future_session.result()
    print(f"Client received session key {session_key}")
    assert type(session_key) is str

    message = encode_defunct(text=session_key)
    signed = w3.eth.account.sign_message(message, private_key=TESTING_PRIVATE_KEY)

    future = asyncio.get_running_loop().create_future()

    async def verify_completed(*args):
        print("Client received verification data", args)
        future.set_result(args)

    print("Client started verification")
    await socket_client.emit(
        "verify_signature",
        data={"signature": signed.signature.hex(), "address": TESTING_ADDRESS},
        callback=verify_completed,
    )

    # wait for the result to be set (avoid waiting forever)
    await asyncio.wait_for(future, timeout=0.5)

    status, session_ley_from_server = future.result()
    assert status == "verification_completed"
    assert session_key == session_ley_from_server

    print("Client disconnected from server")
    await socket_client.disconnect()
