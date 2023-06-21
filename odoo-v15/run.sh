ODOO="15.0"

rm -fR addons
install -d addons/oca

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
