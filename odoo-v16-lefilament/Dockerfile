FROM python:3.11-slim-bullseye AS builder
RUN set -x; \
  apt-get update \
  && apt-get install --yes --no-install-recommends build-essential libldap2-dev libpq-dev libsasl2-dev \
  && pip install wheel \
  && pip wheel --wheel-dir=/svc/wheels --requirement 'https://raw.githubusercontent.com/oca/OCB/16.0/requirements.txt' \
  # astor required by base_view_inheritance_extension
  # openupgradelib required for OCA module migration from one version to another
  # phonenumbers required by phone_validation
  # python-stdnum>=1.18 required by l10n_fr_siret and l10n_fr_siret_lookup
  # PyYAML required by custom scripts for adding modules (https://sources.le-filament.com/lefilament/ansible-roles/docker_odoo/-/tree/master/templates)
  # zxcvbn required by password_security
  && pip wheel --wheel-dir=/svc/wheels 'astor' 'openupgradelib' 'phonenumbers' 'python-stdnum>=1.18' 'PyYAML' 'zxcvbn'


FROM python:3.11-slim-bullseye AS final
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PGDATABASE=odoo

RUN set -x; \
  apt-get update \
  && apt-get install --yes --no-install-recommends \
    curl \
    git \
    gnupg \
    openssh-client \
    xmlsec1 \
  && echo 'deb http://apt.postgresql.org/pub/repos/apt/ bullseye-pgdg main' >> /etc/apt/sources.list.d/postgresql.list \
  && curl -SL https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
  && curl -o wkhtmltox.deb -SL https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.bullseye_amd64.deb \
  && echo 'cecbf5a6abbd68d324a7cd6c51ec843d71e98951 wkhtmltox.deb' | sha1sum -c - \
  && apt-get update \
  && apt-get install --yes --no-install-recommends ./wkhtmltox.deb \
  && apt-get install --yes --no-install-recommends postgresql-client \
  && apt-get --yes autoremove \
  && rm -rf /var/lib/apt/lists/* wkhtmltox.deb

COPY --from=builder /svc /svc
RUN pip3 install --no-index --find-links=/svc/wheels --requirement 'https://raw.githubusercontent.com/oca/OCB/16.0/requirements.txt' \
  && pip3 install --upgrade --no-index --find-links=/svc/wheels 'astor' 'openupgradelib' 'phonenumbers' 'python-stdnum>=1.18' 'PyYAML' 'zxcvbn'

ARG SAVE_COMMITS_DIR='/opt/odoo_commits/'
ENV SAVE_COMMITS_DIR=$SAVE_COMMITS_DIR

# Add Git Known Hosts
COPY ./ssh_known_git_hosts /root/.ssh/known_hosts

# Install Odoo and remove not French translations and .git directory to limit amount of data used by container
ARG SAVE_COMMITS_FILENAME='ocb'
RUN set -x; \
  repo='https://github.com/OCA/OCB' \
  branch='16.0' \
  && useradd --create-home --home-dir /opt/odoo --no-log-init odoo \
  && /bin/bash -c "mkdir -p /opt/odoo/{etc,odoo,additional_addons,private_addons,data,private}" \
  && mkdir /opt/odoo_commits \
  && git clone --single-branch --branch "${branch}" --depth 1 "${repo}" /tmp/repo \
    && commit="$(git -C /tmp/repo rev-parse HEAD)" \
    && mv /tmp/repo/* /opt/odoo/odoo/ \
    && echo "repo;ref;commit" > $SAVE_COMMITS_DIR/$SAVE_COMMITS_FILENAME \
    && echo "${repo};${branch};${commit}" >> $SAVE_COMMITS_DIR/$SAVE_COMMITS_FILENAME \
  && rm -r /tmp/repo \
  # Only keep French translations.
  && find /opt/odoo/odoo/addons/*/i18n/ /opt/odoo/odoo/odoo/addons/base/i18n/ -type f -not -name 'fr.po' -delete \
  && echo "info: OCB commit:" \
  && cat $SAVE_COMMITS_DIR/$SAVE_COMMITS_FILENAME

# Add script to download Odoo addons.
COPY ./get_addons /usr/local/bin

# Install Odoo OCA default dependencies - Commented modules do not exist yet
ARG SAVE_COMMITS_FILENAME='default_addons'
RUN set -x; \
  get_addons 'https://github.com/OCA/account-financial-tools' '16.0' 'additional_addons' \
      account_lock_date_update \
      account_move_name_sequence \
      account_usability \
  && get_addons 'https://github.com/OCA/account-invoicing' '16.0' 'additional_addons' \
      sale_timesheet_invoice_description \
  && get_addons 'https://github.com/OCA/account-reconcile' '16.0' 'additional_addons' \
      account_statement_base \
      account_reconcile_oca \
  && get_addons 'https://github.com/OCA/bank-statement-import' '16.0' 'additional_addons' \
      account_statement_import_base \
      account_statement_import_file \
      account_statement_import_file_reconcile_oca \
      account_statement_import_ofx \
  && get_addons 'https://github.com/OCA/crm' '16.0' 'additional_addons' \
      crm_stage_probability \
  && get_addons 'https://github.com/OCA/l10n-france' '16.0' 'additional_addons' \
      l10n_fr_siret \
      l10n_fr_siret_lookup \
  && get_addons 'https://github.com/OCA/partner-contact' '16.0' 'additional_addons' \
      partner_disable_gravatar \
      partner_firstname \
  && get_addons 'https://github.com/OCA/project' '16.0' 'additional_addons' \
      project_task_default_stage \
      project_template \
  && get_addons 'https://github.com/OCA/server-auth' '16.0' 'additional_addons' \
      password_security \
  && get_addons 'https://github.com/OCA/server-brand' '16.0' 'additional_addons' \
      disable_odoo_online \
      portal_odoo_debranding \
      remove_odoo_enterprise \
  && get_addons 'https://github.com/OCA/server-tools' '16.0' 'additional_addons' \
      base_view_inheritance_extension \
      module_change_auto_install \
  && get_addons 'https://github.com/OCA/server-ux' '16.0' 'additional_addons' \
      server_action_mass_edit \
  && get_addons 'https://github.com/OCA/social' '16.0' 'additional_addons' \
      mail_debrand \
      mail_tracking \
  && get_addons 'https://github.com/OCA/web' '16.0' 'additional_addons' \
      web_chatter_position \
      web_environment_ribbon \
      web_refresher \
      web_responsive \
      web_no_bubble \
      web_theme_classic \
  # Only keep French translations.
  && find /opt/odoo/additional_addons/*/i18n/ -type f -not -name 'fr.po' -delete \
  # Install Le Filament default addons.
  && get_addons 'https://sources.le-filament.com/lefilament/remove_login_links.git' '16.0' 'private_addons/remove_login_links' \
  && get_addons 'https://sources.le-filament.com/lefilament/lefilament_release_agent.git' '16.0' 'private_addons/lefilament_release_agent' \
  && get_addons 'https://sources.le-filament.com/lefilament/restrict_access_rights.git' '16.0' 'private_addons/restrict_access_rights' \
  && echo "info: default addon commits:" \
  && cat $SAVE_COMMITS_DIR/$SAVE_COMMITS_FILENAME

# Copy entrypoint script and Odoo configuration file
COPY ./entrypoint.sh /
COPY ./odoo.conf /opt/odoo/etc/odoo.conf
RUN chown -R odoo:odoo /opt/odoo

# Mount /opt/odoo/data to allow restoring filestore
VOLUME ["/opt/odoo/data/"]

# Expose Odoo services
EXPOSE 8069

# Set default user when running the container
USER odoo

# Start
ENTRYPOINT ["/entrypoint.sh"]
CMD ["odoo"]

# Metadata
LABEL org.label-schema.schema-version="16.0" \
      org.label-schema.vendor=LeFilament \
      org.label-schema.license=Apache-2.0 \
      org.label-schema.vcs-url="https://sources.le-filament.com/lefilament/odoo_docker"
