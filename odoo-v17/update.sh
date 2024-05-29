ODOO="17.0"

install -d addons/oca
install -d filestore

for oca in account-invoicing
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

docker restart odoo-v17_web_1
