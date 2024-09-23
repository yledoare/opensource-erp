# Basic Odoo docker including OCB 10.0/12.0/14.0/15.0/16.0 and some of OCA repos/addons

These docker images are now maintained on [Le Filament GitLab server](https://sources.le-filament.com/lefilament/odoo_docker)

# Description

This Docker is inspired from the ones from [Odoo](https://github.com/odoo/docker), [Tecnativa](https://github.com/Tecnativa/doodba) and [Elico Corporation](https://github.com/Elico-Corp/odoo-docker).

It creates a functional Odoo Docker of limited size (< 400 MB), including Odoo 10.0 or 12.0 or 14.0 or 15.0 or 16.0 from [OCA/OCB](https://github.com/oca/ocb), and also a few addons from [OCA](https://github.com/oca) + addons from [Le Filament](https://sources.le-filament.com/lefilament).

In order to reduce as much as possible the size of the Docker, only French translations are kept and .git directories are removed.
For people needing other languages than English or French, a 12.0_ml image is also provided (only for v12.0 though).

The following Python versions are used :

 - Odoo 10.0 : Python 2.7
 - Odoo 12.0 : Python 3.5.3
 - Odoo 14.0 : Python 3.9
 - Odoo 15.0 : Python 3.10
 - Odoo 16.0 : Python 3.11

Also a specific Python 3.6 version for Odoo v12.0 is generated with tag 12.0_py3.6


The following OCA addons are included by default in this image (in v16.0):
```yaml
  - repo: account-financial-tools
    modules:
     - account_lock_date_update
     - account_move_name_sequence
     - account_usability
  - repo: account-reconcile
    modules:
     - account_statement_base
     - account_reconcile_oca
  - repo: bank-statement-import
    modules:
     - account_statement_import_base
     - account_statement_import_file
     - account_statement_import_ofx
  - repo: partner-contact
    modules:
     - partner_disable_gravatar
     - partner_firstname
  - repo: project
    modules:
     - project_task_default_stage
     - project_template
  - repo: server-auth
    modules:
     - password_security
  - repo: server-brand
    modules:
     - disable_odoo_online
     - portal_odoo_debranding
     - remove_odoo_enterprise
  - repo: server-tools
    modules:
     - base_view_inheritance_extension
     - module_change_auto_install
  - repo: server-ux
    modules:
     - server_action_mass_edit
  - repo: social
    modules:
     - mail_debrand
     - mail_tracking
  - repo: web
    modules:
     - web_chatter_position
     - web_environment_ribbon
     - web_refresher
     - web_responsive
     - web_no_bubble
     - web_theme_classic
```

# Usage


This docker is built every nigth and pushed on [DockerHub](https://hub.docker.com/r/lefilament/odoo) and can be pulled by executing the following command:
```
docker pull lefilament/odoo:10.0
docker pull lefilament/odoo:12.0
docker pull lefilament/odoo:12.0_ml
docker pull lefilament/odoo:12.0_py3.6
docker pull lefilament/odoo:14.0
docker pull lefilament/odoo:15.0
docker pull lefilament/odoo:16.0
```

Note that not Odoo maintained versions (v10.0, v12.0) are not updated nightly like the other ones since there are almost no change on corresponding codes. These versions might be updated in case security fixes are added to corresponding code.

It can also serve as base for deployments as described in this [Ansible role](https://sources.le-filament.com/lefilament/ansible-roles/docker_odoo)

docker-compose example is provided below:
```yaml
version: "2.1"
services:
    odoo:
        image: lefilament/odoo:16.0
        container_name: odoo16
        depends_on:
            - db
        tty: true
        volumes:
            - filestore:/opt/odoo/data:z
        restart: unless-stopped
        command:
            - odoo

    db:
        image: postgres:14-alpine
        container_name: odoo16_db
        environment:
            POSTGRES_USER: "odoo"
            POSTGRES_PASSWORD: "odoo"
        volumes:
            - db:/var/lib/postgresql/data:z
        restart: unless-stopped

networks:
    default:
        driver_opts:
            encrypted: 1

volumes:
    filestore:
    db:
```

# Credits

## Contributors

* Remi Cazenave <remi-filament>


## Maintainer

[![](https://le-filament.com/img/logo-lefilament.png)](https://le-filament.com "Le Filament")

This role is maintained by Le Filament
