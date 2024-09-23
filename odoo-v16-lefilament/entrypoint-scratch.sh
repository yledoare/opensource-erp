#!/bin/sh

# set the postgres database host, port, user and password according to the environment
# and pass them as arguments to the odoo process if not present in the config file
: ${HOST:=${DB_PORT_5432_TCP_ADDR:='db'}}
: ${PORT:=${DB_PORT_5432_TCP_PORT:=5432}}
: ${USER:=${DB_ENV_POSTGRES_USER:=${POSTGRES_USER:='odoo'}}}
: ${PASSWORD:=${DB_ENV_POSTGRES_PASSWORD:=${POSTGRES_PASSWORD:='odoo'}}}

check_config() {
    param="$1"
    value="$2"
    if ! grep -q -E "^\s*\b${param}\b\s*=" /opt/odoo/etc/odoo.conf ; then
        DB_ARGS="${DB_ARGS} --${param} ${value}"
    fi;
}

unaccent_db() {
    /usr/bin/python3 -c "import psycopg2

try:
    conn = psycopg2.connect(database='postgres', user='${USER}', password='${PASSWORD}', host='${HOST}', port='${PORT}')
except:
    print('err: init: fail to connect to database')
    exit(11)

cur = conn.cursor()
try:
    cur.execute(\"SELECT datname FROM pg_database WHERE datname='${PGDATABASE}'\")
except:
    print('err: init: fail to execute request')
    cur.close()
    conn.close()
    exit(12)

if not cur.fetchall():
    cur.close()
    conn.close()
    exit(1)

try:
    cur.execute('CREATE EXTENSION IF NOT EXISTS unaccent')
except:
    print('err: init: fail to execute request')
    cur.close()
    conn.close()
    exit(13)

conn.commit()
cur.close()
conn.close()
exit(0)"

    return $?
}

DB_ARGS=''
check_config "db_host" "$HOST"
check_config "db_port" "$PORT"
check_config "db_user" "$USER"
check_config "db_password" "$PASSWORD"

unaccent_db
return_code=$?
[ "$return_code" -gt 10 ] && exit 1
if [ "$return_code" == 1 ]; then
  	echo "info: init: database $PGDATABASE does not exist"
  	DB_ARGS="${DB_ARGS} --load-language fr_FR"
fi

case "$1" in
    -- | odoo)
        shift
        if [[ "$1" == "scaffold" ]] ; then
            exec /opt/odoo/odoo/odoo-bin -c /opt/odoo/etc/odoo.conf "$@"
        else
            exec /opt/odoo/odoo/odoo-bin -c /opt/odoo/etc/odoo.conf "$@" ${DB_ARGS}
        fi
        ;;
    -*)
        exec /opt/odoo/odoo/odoo-bin -c /opt/odoo/etc/odoo.conf "$@" ${DB_ARGS}
        ;;
    *)
        exec "$@"
esac

exit 1
