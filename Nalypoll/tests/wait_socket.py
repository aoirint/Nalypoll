from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent / 'utils'))

import time
import threading

from socketutil import open_socket, wait_socket

import unittest

class TestWaitSocket(unittest.TestCase):
    def test(self):
        host = 'localhost'
        port = 32767

        def _wait_socket(**kwargs):
            wait_socket(**kwargs)
            print('wait exit')

        def _open_socket(**kwargs):
            open_socket(**kwargs)
            print('open exit')

        wait = threading.Thread(target=_wait_socket, kwargs={
            'host': host,
            'port': port,
        }, daemon=True)
        wait.start()

        time.sleep(1.0)
        self.assertTrue(wait.is_alive())

        server = threading.Thread(target=_open_socket, kwargs={
            'host': host,
            'port': port,
        }, daemon=True)
        server.start()

        # server.join()
        # wait.join()
        time.sleep(1.0)
        self.assertFalse(wait.is_alive())

if __name__ == '__main__':
    unittest.main()
