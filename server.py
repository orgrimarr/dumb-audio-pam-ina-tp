from flask import Flask, request, render_template, json, send_file, Response, make_response, jsonify
from flask_expects_json import expects_json
from jsonschema import ValidationError
from uuid import uuid4
from datetime import datetime
import os
from dotenv import load_dotenv
import boto3

load_dotenv()

S3_HOST = os.getenv('CELLAR_ADDON_HOST')
S3_KEY = os.getenv('CELLAR_ADDON_KEY_ID')
S3_SECRET = os.getenv('CELLAR_ADDON_KEY_SECRET')
S3_BUCKET = os.getenv('CELLAR_BUCKET') if os.getenv(
    'CELLAR_BUCKET') else "pam-medias"
PORT = int(os.getenv('PORT')) if os.getenv('PORT') else 5000

s3 = boto3.client(
    's3',
    endpoint_url=f"https://{S3_HOST}",
    aws_access_key_id=S3_KEY,
    aws_secret_access_key=S3_SECRET
)

assets = [{"id": "example", "title": "Demo PAM", "author": "Julien", "body": "Demo",
           "date": "2022-10-18T10:50:47.350Z"}]

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


def s3_get_download_url(asset_id):
    media_key = f"audio/{asset_id}.mp3"
    result = s3.list_objects(
        Bucket=S3_BUCKET, Prefix=media_key, Delimiter='/', MaxKeys=1)
    if 'Contents' in result:
        for obj in result['Contents']:
            if obj['Key'] == media_key:
                url = s3.generate_presigned_url(
                    ClientMethod='get_object',
                    Params={
                        'Bucket': S3_BUCKET,
                        'Key': media_key
                    }
                )
                return url, media_key
    return None, media_key


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
    return json.dumps(new_asset)


@app.route('/assets/<asset_id>/media_status', methods=['GET'])
def get_asset_media_status(asset_id):
    media_uri, media_key = s3_get_download_url(asset_id)
    if (media_uri):
        return json.dumps({"status": f"Media available in s3 storage. ({media_key})", "uri": media_uri})
    else:
        return json.dumps({"status": f"Media {asset_id} not found.  ({media_key})"})


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
    app.run(port=PORT)
