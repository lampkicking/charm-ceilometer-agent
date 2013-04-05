#!/usr/bin/python

import sys
import time
import os
import utils
import ceilometer_utils


def install():
    utils.configure_source()
    utils.install(*ceilometer_utils.CEILOMETER_AGENT_PACKAGES)
    ceilometer_utils.modify_config_file(ceilometer_utils.NOVA_CONF, 
        ceilometer_utils.NOVA_SETTINGS)

    port = ceilometer_utils.CEILOMETER_PORT
    utils.expose(port)


def get_conf():
    for relid in utils.relation_ids('ceilometer-service'):
        for unit in utils.relation_list(relid):
            conf = {
                "rabbit_host": utils.relation_get('rabbit_host', unit, relid),
                "rabbit_virtual_host": ceilometer_utils.RABBIT_VHOST,
                "rabbit_userid": ceilometer_utils.RABBIT_USER,
                "rabbit_password": utils.relation_get('rabbit_password', unit, relid),
                "keystone_os_username": utils.relation_get('keystone_os_username', unit, relid),
                "keystone_os_password": utils.relation_get('keystone_os_password', unit, relid),
                "keystone_os_tenant": utils.relation_get('keystone_os_tenant', unit, relid),
                "keystone_host": utils.relation_get('keystone_host', unit, relid),
                "keystone_port": utils.relation_get('keystone_port', unit, relid),
                "metering_secret": utils.relation_get('metering_secret', unit, relid)
            }
            if None not in conf.itervalues():
                return conf
    return None

def render_ceilometer_conf(context):
    if (context and os.path.exists(ceilometer_utils.CEILOMETER_CONF)):
        # merge contexts
        context['service_port'] = ceilometer_utils.CEILOMETER_PORT
        context['ceilometer_host'] = utils.get_unit_hostname()

        with open(ceilometer_utils.CEILOMETER_CONF, "w") as conf:
            conf.write(utils.render_template(
                os.path.basename(ceilometer_utils.CEILOMETER_CONF), context))

        utils.restart(*ceilometer_utils.CEILOMETER_COMPUTE_SERVICES)
        return True
    return False


def ceilometer_changed():
    # check if we have rabbit and keystone already set
    context = get_conf()
    if context:
            render_ceilometer_conf(context)
    else:
        # still waiting
        utils.juju_log("INFO", "ceilometer: rabbit and keystone " +
            "credentials not yet received from peer.")


utils.do_hooks({
    "install": install,
    "ceilometer-service-relation-changed": ceilometer_changed
})
sys.exit(0)
