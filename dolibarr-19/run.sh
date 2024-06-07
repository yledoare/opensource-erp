DOLIBARR=19.0.2
[ ! -e $DOLIBARR.tar.gz ] && wget https://github.com/Dolibarr/dolibarr/archive/refs/tags/$DOLIBARR.tar.gz
[ ! -e dolibarr-$DOLIBARR ] && tar xzvf $DOLIBARR.tar.gz
cd dolibarr-$DOLIBARR 
install -d build/docker
cd build/docker
rm docker-compose.yml
wget https://raw.githubusercontent.com/Dolibarr/dolibarr/develop/build/docker/docker-compose.yml
sed -i 's/3306:3306/3319:3306/' docker-compose.yml
sed -i 's/8080:80/8119:80/' docker-compose.yml
sed -i 's/80:80/8019:80/' docker-compose.yml
sed -i 's/9000:9000/9019:9000/' docker-compose.yml
sed -i 's/8081:1080/8219:1080/' docker-compose.yml
sed -i 's/25:1025/2518:1025/' docker-compose.yml
sed -i 's/host-gateway/127.0.0.1/' docker-compose.yml
sed -i 's/rootpassfordev/rootpwd/' docker-compose.yml
sed -i 's/build: ./image: dolibarr-develop/' docker-compose.yml
sed -i 's/web:/web19:/' docker-compose.yml
sed -i 's/mail:/mail19:/' docker-compose.yml
sed -i 's/phpmyadmin:/phpmyadmin19:/' docker-compose.yml
sed -i 's/mariadb:/mariadb19:/' docker-compose.yml
sed -i 's/mariadb19:latest/mariadb:latest/' docker-compose.yml
sed -i 's/- mail/- mail19/g' docker-compose.yml
sed -i 's/- mariadb/- mariadb19/g' docker-compose.yml
HOST_USER_ID=$(id -u) docker-compose up -d
