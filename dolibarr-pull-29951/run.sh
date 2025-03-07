commit=fd5430c9d9ed6399356295f1db5332e222587b9e

[ ! -e dolibarr ] && git clone https://github.com/Dolibarr/dolibarr.git
cd dolibarr
git checkout $commit

cd build/docker 

sed -i 's/mariadb:latest/mariadb:latest/' docker-compose.yml


export HOST_USER_ID=$(id -u)
export HOST_GROUP_ID=$(id -g)
export MYSQL_ROOT_PWD=$(tr -dc A-Za-z0-9 </dev/urandom | head -c 13; echo)

docker-compose up -d
