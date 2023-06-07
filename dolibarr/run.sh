DOLIBARR=17.0.2
[ ! -e $DOLIBARR.tar.gz ] && wget https://github.com/Dolibarr/dolibarr/archive/refs/tags/$DOLIBARR.tar.gz
[ ! -e dolibarr-$DOLIBARR ] && tar xzvf $DOLIBARR.tar.gz
cd build/docker
HOST_USER_ID=$(id -u) docker-compose up -d
