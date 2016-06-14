#!/usr/bin/python
'''
Author: Adi Chiru (achiru@ea.com)

Description: This script is used to update the manifest files with new details after the build step.
This ensures that at any moment in time the manifest file describes exactly the product.
If used with the master branch or a release branch will work the same and will give a "snapshot"
of the product development at a specific moment in time.

This script is to be used either from a Jenkins job after the [product]_manifest.json file was checkedout.
Suports Perforce and Github as SCM systems
If used with Perforce, it requires the P4CLIENT variable's value to make the changes to the manifest file.
If used with Github ???

The manifest file to update is passed as a parameter to this script.
'''

import logging
import argparse
import os
import sys
import json
import collections
import datetime
import time
from P4 import P4, P4Exception

scm = 'perforce'
#scm = 'github'

p4_port = '???'
p4_user = '???'
p4_password = '???'
p4_client = os.getenv('P4CLIENT')

script_name = os.path.basename(__file__)
log_file_name = str(script_name) + '.log'
logging.basicConfig(filename=log_file_name,level=logging.DEBUG)
now = datetime.datetime.now()


def checkPrerequisites( manifest_file ):
    #check if the manifest file exists; it should be in the workspace since the check out is done by the Jenkins plugin
    check_file = os.path.isfile(manifest_file)
    if check_file != 'True':
        logging.critical('Error: manifest file not found. Exiting...')
        sys.exit(1)

def computeTimestamp():
    timestamp = int(time.time())
    return str(timestamp)

def updateProductDetailsInMnifest( manifest_file, d_name, d_value ):
    with open(manifest_file, 'r+') as json_data:
        manifest_json_object = json.load(json_data, object_pairs_hook=collections.OrderedDict)
        for product_key, product_value in manifest_json_object.items():
            if str(product_key) == str(d_name):
                manifest_json_object[product_key] = d_value
                logging.info('Updated %s for product to %s', d_name, d_value)
        json_data.seek(0)
        json_data.write(json.dumps(manifest_json_object, sort_keys=False, indent=4, separators=(',', ':')))
        json_data.truncate()
    return str(manifest_file)

def updateComponentDetailsInManifest( manifest_file, component, d_name, d_value ):
    with open(manifest_file, 'r+') as json_data:
        manifest_json_object = json.load(json_data, object_pairs_hook=collections.OrderedDict)
        logging.info('Selected component to modify is %s', component)
        logging.info('    - %s to update to is %s', d_name, d_value)
        for akey, avalue in manifest_json_object.items():
            if str(akey) == 'components':
                for component_name_key, component_name_value in avalue.items():
                    if str(component_name_key) == str(component):
                        for details_key, details_value in component_name_value.items():
                            if str(details_key) == str(d_name):
                                logging.info('Current %s for %s is %s', d_name, component, details_value)
                                manifest_json_object[akey][component_name_key][details_key] = d_value
                            else:
                                logging.error('Given detail name (%s) not found in the manifest.', d_name)
                    else:
                        logging.error('Given component (%s) not found in the manifest.', component)
        json_data.seek(0)
        json_data.write(json.dumps(manifest_json_object, sort_keys=False, indent=4, separators=(',', ':')))
        json_data.truncate()
    return str(manifest_file)

def p4_init(p4_port, p4_client, p4_user, p4_password):
    global p4
    p4 = P4()
    p4.port = p4_port
    p4.user = p4_user
    p4.password = p4_password
    p4.charset = "utf8"
    p4.client = p4_client
    p4.connect()
    p4.run_login()
    opened = p4.run_opened()

def p4_edit_manifest(manifest_file, component, version, changelist, p4_location):
    global new_changelist
    if str(component) == 'None':
        submit_message = 'Auto updating the manifest for Product (version: {v}).'.format(v=version)
    else:
        submit_message = 'Auto updating the manifest for {s} (version: {v}, changelist: {c}, p4_location: {b}).'.format(s=component, v=version, c=changelist, b=p4_location)
    new_changelist = p4.fetch_change()
    p4.run_edit(manifest_file)
    new_changelist["Description"] = str(submit_message)
    new_changelist["Files"] = [manifest_file]

def p4_submit_change():
    p4.input = new_changelist
    p4.run("submit", "-i")

def main( manifest_file, product, component, version, changelist, p4_location, timestamp, submit ):
    '''
    The only valid/useful ways to call this script are as follows:
    $python_bin update_manifest.py --manifest_file ${manifest_file} --product --version ${version}
    $python_bin update_manifest.py --manifest_file ${manifest_file} --product --version ${version} --changelist ${changelist} --timestamp
    $python_bin update_manifest.py --manifest_file ${manifest_file} --component ${component} --version ${version} --changelist ${changelist} --p4_location ${p4_location} --submit
    However, we need to be sure we account for missing parameters.
    '''
    logging.info('----- New run: %s -----', now)
    if product:
        if version:
            manifest_file_to_submit = updateProductDetailsInMnifest(manifest_file, 'version', version)
        if changelist:
            manifest_file_to_submit = updateProductDetailsInMnifest(manifest_file, 'changelist', changelist)
        if timestamp:
            ts_value = computeTimestamp()
            manifest_file_to_submit = updateProductDetailsInMnifest(manifest_file, 'timestamp', ts_value)

    if component:
        if version:
            manifest_file_to_submit = updateComponentDetailsInManifest(manifest_file, component, 'version', version)
        if changelist:
            manifest_file_to_submit = updateComponentDetailsInManifest(manifest_file, component, 'changelist', changelist)
        if p4_location:
            manifest_file_to_submit = updateComponentDetailsInManifest(manifest_file, component, 'p4_location', p4_location)

    if submit:
        p4_init(p4_port, p4_client, p4_user, p4_password)
        manifest_file_name = os.path.basename(manifest_file_to_submit)
        product_name, ignore_rest = str(manifest_file_name).split("-", 1)
        manifest_file_depot_path = p4_location + '/' + manifest_file_name
        p4_edit_manifest(manifest_file_depot_path, component, version, changelist, p4_location)
        p4_submit_change()
        p4.disconnect()

if __name__=="__main__":
    parser = argparse.ArgumentParser(prog='[script name]',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-m', '--manifest_file', dest='manifest_file', required=True, help='The manifest file to update. This is how you point to either the master manifest or a release manifest file.')
    parser.add_argument('-p', '--product', action='store_true', required=False, help='The product for which the manifest file needs updating. TEMPORARY')
    parser.add_argument('-s', '--component', dest='component', required=False, help='The component for which the update is required. If ommited or empty the update is done on product.')
    parser.add_argument('-v', '--version', dest='version', required=False, help='The new version for the specified component.')
    parser.add_argument('-c', '--changelist', dest='changelist', required=False, help='The new changelist for the specified component.')
    parser.add_argument('-b', '--p4_location', dest='p4_location', required=False, help='The P4 location to use to build the specified component.')
    parser.add_argument('-t', '--timestamp', action='store_true', required=False, help='If specified, update the timestamp.')
    parser.add_argument('-u', '--submit', action='store_true', required=False, help='If specified, submit the changes to Perforce otherwise skip this step.')
    args = vars(parser.parse_args())

    main(str(args['manifest_file']), args['product'], str(args['component']), str(args['version']), str(args['changelist']), str(args['p4_location']), args['timestamp'], args['submit'])
