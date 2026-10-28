"""Reviewed single-worker loopback entry point. No migration or data mutation."""
import argparse
import os
import uvicorn


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Validate configuration and database without binding a socket')
    args = parser.parse_args()
    if os.environ.get('APP_ENV') not in ('development', 'production'):
        raise SystemExit('Set APP_ENV explicitly before using the deployment entry point')
    from .main import security, engine
    from .deployment import database_ready, operation_event
    if not security.synthetic_demo:
        raise SystemExit('This deployment entry point requires DATA_MODE=synthetic; use the local-development instructions otherwise')
    try:
        port = int(os.getenv('PORT', '8015'))
        if not 1024 <= port <= 65535:
            raise ValueError()
    except ValueError:
        raise SystemExit('PORT must be an integer from 1024 to 65535') from None
    if not database_ready(engine, True):
        operation_event('startup_blocked')
        raise SystemExit('Dedicated demonstration database is not ready')
    if args.check:
        print('Synthetic demonstration configuration and database are ready')
        return
    uvicorn.run('app.main:app', host='127.0.0.1', port=port, workers=1, access_log=False,
        proxy_headers=security.production, forwarded_allow_ips='127.0.0.1', log_level='warning')


if __name__ == '__main__':
    main()
