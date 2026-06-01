from backend.app_factory import create_app

app = create_app()

if __name__ == '__main__':
    import os
    port = os.environ.get('FLASK_RUN_PORT', 5000)
    debug_mode = os.environ.get('FLASK_ENV', 'production') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
