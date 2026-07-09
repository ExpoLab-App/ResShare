from backend.app_factory import create_app

app = create_app()

if __name__ == '__main__':
    import os

    debug_mode = os.environ.get('FLASK_ENV', 'production') != 'production'
    run_port = int(os.environ.get('FLASK_RUN_PORT', 5000))
    app.run(host='0.0.0.0', port=run_port, debug=debug_mode)
