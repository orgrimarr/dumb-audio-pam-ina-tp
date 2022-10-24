# dumb-audio-pam-ina-tp

Dumb simple PAM like API used in INA tp

Hosted on CleverCloud :

- Python nano instance
- PG SQL addon
- Cellar addon

## App configuration

Var env

```env
PORT=5000

CELLAR_BUCKET=pam-medias
CELLAR_ADDON_HOST=
CELLAR_ADDON_KEY_ID=
CELLAR_ADDON_KEY_SECRET=

POSTGRESQL_ADDON_DB=
POSTGRESQL_ADDON_HOST=
POSTGRESQL_ADDON_PASSWORD=
POSTGRESQL_ADDON_PORT=
POSTGRESQL_ADDON_USER=
```

Assets are stored on PG

Medias (audio) are stored on cellar (S3 like). **audio/asset_id.mp3**

## Clever cloud conf

### DB

Init DB using `db_init.sql`

### Cellar

Create a bucket

## Python app

Var env (expert mode) :

```env
CC_PYTHON_MODULE="server:app"
CC_PYTHON_VERSION=3"
CELLAR_BUCKET="BUCKET_NAME"
PORT="8080"
STATIC_FILES_PATH="static/"
STATIC_URL_PREFIX="/static"
```
