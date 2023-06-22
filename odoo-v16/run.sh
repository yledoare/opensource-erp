ODOO="16.0"

install -d addons/oca
install -d filestore

for oca in l10n-france reporting-engine intrastat-extrastat e-commerce  geospatial  manufacture  server-tools
do
  [ ! -e addons/$oca ] && git clone https://github.com/OCA/$oca.git addons/$oca
  cd addons/$oca || exit 1
  git checkout origin/$ODOO || exit 2
  ls | while read module
  do
	  test -f $module && continue
	  # [ "$module" = "setup" ] && continue
	  echo "Module $module"
	  cp -fR $module ../oca
  done 
  cd ../..
done

docker-compose up -d

#4G RAM
sleep 10
docker exec -u root -ti odoo-v16_web_1 sed -i 's/limit_time_real = 120/limit_time_real = 320/' /etc/odoo/odoo.conf
#docker exec -u root -ti odoo-v16_web_1 /bin/sh -c "echo limit_memory_hard = 3684354560 >> /etc/odoo/odoo.conf"
#docker exec -u root -ti odoo-v16_web_1 /bin/sh -c "echo limit_memory_soft = 3184354560 >> /etc/odoo/odoo.conf"
#docker exec -u root -ti odoo-v16_web_1 /bin/sh -c "echo list_db = False >> /etc/odoo/odoo.conf"
docker restart odoo-v16_web_1

sleep 10

docker exec -u root -ti odoo-v16_web_1 apt-get -y update
docker exec -u root -ti odoo-v16_web_1 apt-get -y install procps vim
