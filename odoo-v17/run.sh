ODOO="17.0"

install -d addons/oca
install -d filestore

for oca in server-env account-invoicing helpdesk hr bank-payment community-data-files edi l10n-france reporting-engine intrastat-extrastat e-commerce  geospatial  manufacture  server-tools
do
  [ ! -e addons/$oca ] && git clone --single-branch --branch "${ODOO}" --depth 1 https://github.com/OCA/$oca.git addons/$oca
  cd addons/$oca || exit 1
  ls | while read module
  do
	  [ "$module" = "requirements.txt" ] && cat requirements.txt >> ../oca/requirements.txt
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
#docker-compose exec -u root web /bin/sh -c "echo limit_time_real = 320 >> /etc/odoo/odoo.conf"

docker-compose exec -u root web pip3 install -r /mnt/extra-addons/requirements.txt 
#docker-compose exec -u root web pip3 install python-stdnum==1.18

docker-compose exec -u root web apt-get -y update
docker-compose exec -u root web apt-get -y install procps vim

docker-compose restart web
