#!/usr/bin/python

import argparse
import sys
import os
import glob
import json

def usage():
    print "help message here"

def getManifestAsJson( manifest_file ):
    with open(manifest_file) as file_data:
        json_data = json.load(file_data)
        # if error here, not a valid json format
    return json_data

def getProductName( manifest_file ):
    json_manifest = getManifestAsJson(manifest_file)
    for p_name, p_value in json_manifest.items():
        if str(p_name) == "name":
            product_name = p_value
    return str(product_name)

def getProductDescription( manifest_file ):
    json_manifest = getManifestAsJson(manifest_file)
    for p_name, p_value in json_manifest.items():
        if str(p_name) == "description":
            product_description = p_value
    return str(product_description)

def getProductVersion( manifest_file ):
    json_manifest = getManifestAsJson(manifest_file)
    for p_name, p_value in json_manifest.items():
        if str(p_name) == "version":
            product_version = p_value
    return str(product_version)

def getComponentPerforceLocation( manifest_file, component ):
    json_manifest = getManifestAsJson(manifest_file)
    for p_name, p_value in json_manifest.items():
        if str(p_name) == "components":
            for c_name, c_value in p_value.items():
                if str(c_value) == str(component):
                    for c_parameter_name, c_parameter_value in c_value.items():
                        if str(c_parameter_name) == "p4_location":
                            component_p4_location_name = c_parameter_value
    return str(component_p4_location_name)

def getComponentVersion( manifest_file, component ):
    json_manifest = getManifestAsJson(manifest_file)
    for p_name, p_value in json_manifest.items():
        if str(p_name) == "components":
            for c_name, c_value in p_value.items():
                if str(c_value) == str(component):
                    for c_parameter_name, c_parameter_value in c_value.items():
                        if str(c_parameter_name) == "version":
                            component_version = c_parameter_value
    return str(component_version)

def makeBuildParametersFile( manifest_file, component, build_parameters_file ):
    json_manifest = getManifestAsJson(manifest_file)
    content = 'project_name=' + str(component) + '\n'
    for p_name, p_value in json_manifest.items():
        if str(p_name) == 'components':
            for c_name, c_value in p_value.items():
                if str(c_name) == str(component):
                    for c_parameter_name, c_parameter_value in c_value.items():
                        if str(c_parameter_name) == 'version':
                            component_version = c_parameter_value
                            content += 'build_version_woq=' + str(component_version) + '\n'
                        if str(c_parameter_name) == 'p4_location':
                            component_p4_location = c_parameter_value
                            content += 'p4_location=' + str(component_p4_location) + '\n'
    with open(build_parameters_file, 'w') as f:
        f.write(content)

def main( manifest_file, component, build_parameters_file):
    makeBuildParametersFile(manifest_file, component, build_parameters_file)
    try:
        if os.stat(build_parameters_file).st_size == 0:
            print "Parameters file if empty."
            sys.exit(1)
    except OSError:
        print "Parameters file does not seem to have been created."
        sys.exit(1)


if __name__=="__main__":
    parser = argparse.ArgumentParser(prog='[script name]',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-m', '--manifest_file', dest='manifest_file', required=True, help='The manifest file to read. This is how you point to either the master manifest or a release manifest file.')
    parser.add_argument('-s', '--component', dest='component', required=True, help='The component for which to make the build parameters file.')
    parser.add_argument('-o', '--outfile', dest='build_parameters_file', required=True, help='The parameters file to create for build process.')
    args = vars(parser.parse_args())

    main(str(args['manifest_file']), str(args['component']), str(args['build_parameters_file']))

