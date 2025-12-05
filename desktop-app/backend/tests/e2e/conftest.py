import pytest
import subprocess
import time
import os
import signal
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="session")
def backend_server():
    """Start the backend server for testing"""
    # Assuming we are in backend root
    proc = subprocess.Popen(
        ["python", "app_service.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "TESTING": "true"}
    )
    
    # Wait for server to start
    time.sleep(3)
    
    yield proc
    
    # Cleanup
    if proc.poll() is None:
        proc.terminate()
        proc.wait()

@pytest.fixture(scope="session")
def browser_context(backend_server):
    """Launch browser and create context"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        yield context
        browser.close()
