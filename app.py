from backend.app_factory import create_app

app = create_app()

if __name__ == '__main__':
    import os

    debug_mode = os.environ.get('FLASK_ENV', 'production') != 'production'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
