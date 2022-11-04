from flask import Flask, request, render_template, json, send_file, Response, make_response, jsonify
from flask_expects_json import expects_json
from jsonschema import ValidationError
from uuid import uuid4
from datetime import datetime
import os
from dotenv import load_dotenv
import boto3
from peewee import PostgresqlDatabase, Model, CharField, UUIDField, DateTimeField, DoesNotExist
import psycopg2.extras
load_dotenv()

DB_NAME = os.getenv('POSTGRESQL_ADDON_DB')
DB_HOST = os.getenv('POSTGRESQL_ADDON_HOST')
DB_PASSWORD = os.getenv('POSTGRESQL_ADDON_PASSWORD')
DB_PORT = os.getenv('POSTGRESQL_ADDON_PORT')
DB_USER = os.getenv('POSTGRESQL_ADDON_USER')

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

db = PostgresqlDatabase(DB_NAME, user=DB_USER,
                        password=DB_PASSWORD, host=DB_HOST)
psycopg2.extras.register_uuid()


class BaseModel(Model):
    class Meta:
        database = db


class Assets(BaseModel):
    id = UUIDField(unique=True, primary_key=True)
    title = CharField()
    author = CharField()
    body = CharField()
    date = DateTimeField()


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


def get_medias_key(asset_id):
    return f"audio/{asset_id}.mp3"


def s3_file_exists(asset_id):
    media_key = get_medias_key(asset_id)
    result = s3.list_objects(
        Bucket=S3_BUCKET, Prefix=media_key, Delimiter='/', MaxKeys=1)
    if 'Contents' in result:
        for obj in result['Contents']:
            if obj['Key'] == media_key:
                return media_key
    return None


def s3_get_download_url(asset_id):
    media_key = s3_file_exists(asset_id)
    if media_key:
        url = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': S3_BUCKET,
                'Key': media_key
            }
        )
        return url, media_key
    else:
        return None, get_medias_key(asset_id)


def s3_list_assets():
    asset_list = []
    for asset in Assets.select():
        asset_list.append({'id': asset.id, 'title': asset.title,
                          'author': asset.author, 'body': asset.body, 'date': asset.date})
    return asset_list


def s3_delete(asset_id):
    media_key = get_medias_key(asset_id)
    s3.delete_object(Bucket=S3_BUCKET, Key=media_key)


def s3_save_asset(asset):
    to_save = Assets(id=asset.get('id'), title=asset.get('title'), author=asset.get(
        'author'), body=asset.get('body'), date=asset.get('date'))
    modified_rows = to_save.save(force_insert=True)
    if modified_rows != 1:
        raise Exception('Error saving data to db. No data saved')


app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/assets', methods=['GET'])
def get_assets():
    return json.dumps(s3_list_assets())


@app.route('/assets', methods=['POST'])
@expects_json(asset_schema)
def create_asset():
    now = datetime.now()
    bearer = request.headers.get('authorization')
    if not bearer or bearer != "Bearer super-secure-token":
        return make_response(jsonify({'message': "Unauthorized"}), 401)
    new_asset = request.get_json(force=True)
    new_values = {
        "id": uuid4(),
        "date": now.isoformat()
    }
    new_asset.update(new_values)

    s3_save_asset(new_asset)
    return json.dumps(new_asset)


@app.route('/assets/<asset_id>/media_status', methods=['GET'])
def get_asset_media_status(asset_id):
    media_uri, media_key = s3_get_download_url(asset_id)
    if (media_uri):
        return json.dumps({"status": f"Media available in s3 storage. ({media_key})", "uri": media_uri})
    else:
        return json.dumps({"status": f"Media {asset_id} not found.  ({media_key})"})


@app.route('/assets/<asset_id>', methods=['GET'])
def get_asset(asset_id):
    try:
        asset = Assets.get_by_id(asset_id)
        return json.dumps({'id': asset.id, 'title': asset.title,
                           'author': asset.author, 'body': asset.body, 'date': asset.date})
    except DoesNotExist:
        return make_response(jsonify({'message': f"Asset with id {asset_id} does not exists"}), 404)


@app.route('/assets/<asset_id>', methods=['DELETE'])
def delete_asset(asset_id):
    try:
        bearer = request.headers.get('authorization')
        if not bearer or bearer != "Bearer super-secure-hardcoded-delete-token":
            return make_response(jsonify({'message': "Unauthorized"}), 401)
        s3_delete(asset_id)
        Assets.delete_by_id(asset_id)
        return json.dumps({"id": asset_id})
    except DoesNotExist:
        return make_response(jsonify({'message': f"Asset with id {asset_id} does not exists"}), 404)


@app.errorhandler(400)
def bad_request(error):
    if isinstance(error.description, ValidationError):
        original_error = error.description
        return make_response(jsonify({'message': original_error.message}), 400)
    return make_response(jsonify({'message': error}), 400)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({"message": f"Endpoint {request.method} {request.path} not found"}), 404)


@app.errorhandler(500)
def server_error(error):
    return make_response(jsonify({"message": f"{error}. See logs for more details"}), 500)


if __name__ == '__main__':
    app.run(port=PORT)
