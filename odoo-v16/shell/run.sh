docker cp list-users.py odoo-v16_web_1:.
docker cp shell.sh odoo-v16_web_1:.
docker exec -t odoo-v16_web_1 bash -c '/bin/bash /shell.sh'
# docker exec -ti odoo-v16_web_1 bash -c '/usr/bin/python3 /usr/bin/odoo shell -d test --db_host db --db_port 5432 --db_user odoo --db_password odoo'

