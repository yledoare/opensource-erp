rm -fR addons
install -d addons

# for oca in account-invoicing server-tools # e-commerce  geospatial  manufacture  server-tools # 
for oca in e-commerce
do
  [ ! -e addons/$oca ] && git clone https://github.com/OCA/$oca.git addons/$oca
  cd addons/$oca && git checkout origin/14.0 
  cd ../..
done

for oca in l10n-france
do
  [ ! -e $oca ] && git clone https://github.com/OCA/$oca.git $oca
  cd $oca && git checkout origin/14.0 
  cd ../
done

#install -d addons/server-tools2
#cp -fR addons/server-tools/module_change_auto_install addons/server-tools2 
#pwd

#cp etc/odoo/odoo.conf .
#docker build -f Dockerfile -t odoo-14 .

docker-compose up -d
