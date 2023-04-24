[ ! -e 17.0.1.tar.gz ] && wget https://github.com/Dolibarr/dolibarr/archive/refs/tags/17.0.1.tar.gz
[ ! -e dolibarr-17.0.1 ] && tar xzvf 17.0.1.tar.gz
cd build/docker
HOST_USER_ID=$(id -u) docker-compose up -d
