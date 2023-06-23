ODOO="14.0"

install -d addons/oca
install -d filestore

for oca in bank-payment community-data-files edi l10n-france reporting-engine intrastat-extrastat e-commerce  geospatial  manufacture  server-tools
do
  [ ! -e addons/$oca ] && git clone https://github.com/OCA/$oca.git addons/$oca
  cd addons/$oca || exit 1
  git checkout origin/$ODOO || exit 2
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
docker exec -u root -ti odoo-v14_web_1 sed -i 's/limit_time_real = 120/limit_time_real = 320/' /etc/odoo/odoo.conf
docker exec -u root -ti odoo-v14_web_1 apt-get -y update
docker exec -u root -ti odoo-v14_web_1 apt-get -y install procps vim swig
docker exec -u root -ti odoo-v14_web_1 apt-get -y install libjpeg-dev

docker exec -u root -ti odoo-v14_web_1 pip3 install -r /mnt/addons/requirements.txt 
docker exec -u root -ti odoo-v14_web_1 pip3 install pdfplumber==0.5.0
docker exec -u root -ti odoo-v14_web_1 pip3 install pillow==6.2.2

docker restart odoo-v14_web_1
