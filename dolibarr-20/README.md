# Dolibarr 20

# Installation

```
bash run.sh
```

# Logs

```
docker-compose logs --tail=20 -f framadate
```

# Fix

After install
set $dolibarr_main_force_https='0' and $dolibarr_main_url_root in conf/conf.php 
