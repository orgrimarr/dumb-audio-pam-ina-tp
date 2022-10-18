from flask import Flask, request, render_template, json, send_file, Response, make_response, jsonify
from flask_expects_json import expects_json
from jsonschema import ValidationError
from uuid import uuid4
from datetime import datetime

assets = [{"id": "1", "title": "Demo PAM", "author": "Julien", "body": "Demo",
           "date": "2022-10-18T10:50:47.350Z", "media": {"id": "example"}}]

asset_schema = {
    'type': 'object',
    'properties': {
        'title': {'type': 'string'},
        'author': {'type': 'string'},
        'body': {'type': 'string'}
    },
    'additionalProperties': False,
    'required': ['title', 'author', 'body']

}

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/assets', methods=['GET'])
def get_assets():
    return json.dumps(assets)


@app.route('/assets', methods=['POST'])
@expects_json(asset_schema)
def create_asset():
    now = datetime.now()

    new_asset = request.get_json(force=True)
    new_values = {
        "id": uuid4(),
        "date": now.isoformat()
    }
    new_asset.update(new_values)

    assets.append(new_asset)
    return json.dumps(assets)


@app.route('/asset/<asset_id>/media', methods=['GET'])
def get_asset_media(asset_id):
    if (asset_id == 'example'):
        return send_file('/home/orgrimarr/git/dumb-audio-pam-ina-tp/app/static/audio/bensound-thecalling.mp3', mimetype="audio/mp3", as_attachment=False)
    return Response(status=200, mimetype="audio/mp3")


@app.errorhandler(400)
def bad_request(error):
    if isinstance(error.description, ValidationError):
        original_error = error.description
        return make_response(jsonify({'message': original_error.message}), 400)
    return make_response(jsonify({'message': error}), 400)


@app.errorhandler(404)
def not_found(error):
    return json.dumps({"message": f"Endpoint {request.method} {request.path} not found"})


@app.errorhandler(500)
def server_error(error):
    return json.dumps({"message": f"{error}. See logs for more details"})


if __name__ == '__main__':
    app.run()
