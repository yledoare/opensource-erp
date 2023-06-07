[ ! -e dolibarr-git ] && git clone https://github.com/Dolibarr/dolibarr dolibarr-git
cd dolibarr-git/build/docker
git checkout docker-compose.yml
sed -i 's/3306:3306/3307:3306/' docker-compose.yml
sed -i 's/8080:80/8089:80/' docker-compose.yml
sed -i 's/80:80/8071:80/' docker-compose.yml
sed -i 's/9000:9000/9001:9001/' docker-compose.yml
sed -i 's/25:25/2525:2525/' docker-compose.yml
sed -i 's/host-gateway/127.0.0.1/' docker-compose.yml
sed -i 's/rootpassfordev/rootpwd/' docker-compose.yml
HOST_USER_ID=$(id -u) docker-compose up -d
#  docker exec -ti docker_mariadb_1 mysql -u root -proot dolibarr
