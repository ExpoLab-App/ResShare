from flask import jsonify


def register_health_routes(app, logger):
    @app.route('/', methods=['GET'])
    def health_route():
        return jsonify({'message': 'OK'}), 200
