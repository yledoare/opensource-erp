DOLIBARR=20.0.4
[ ! -e $DOLIBARR.tar.gz ] && wget https://github.com/Dolibarr/dolibarr/archive/refs/tags/$DOLIBARR.tar.gz
[ ! -e dolibarr-$DOLIBARR ] && tar xzvf $DOLIBARR.tar.gz
cd dolibarr-$DOLIBARR 

sed -i 's@force_install_main_data_root = null@force_install_main_data_root = '/var/documents'@' htdocs/install/install.forced.docker.php 

install -d build/docker

cp ../docker-compose.yml build/docker
cp ../Dockerfile build/docker
cp ../docker-run.sh build/docker

cd build/docker

export HOST_USER_ID=$(id -u)
export HOST_GROUP_ID=$(id -g)
export MYSQL_ROOT_PWD=$(tr -dc A-Za-z0-9 </dev/urandom | head -c 13; echo)

echo "MYSQL_ROOT_PWD is $MYSQL_ROOT_PWD"
docker-compose up -d
