import argparse
import asyncio
import aiohttp
import uvloop
from app.settings import load_config
from app.app import create_app

parser = argparse.ArgumentParser(description='Start REST service')
parser.add_argument(
    '--host',
    help='Host to listen',
    default='0.0.0.0'
)
parser.add_argument(
    '--port',
    help='Port to listen',
    default=8080
)
parser.add_argument(
    '-c', '--config',
    type=argparse.FileType('r'),
    help='Path to configuration file'
)

args = parser.parse_args()


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
app = create_app(config=load_config(args.config))

if __name__ == '__main__':
    aiohttp.web.run_app(app, host=args.host, port=args.port)
