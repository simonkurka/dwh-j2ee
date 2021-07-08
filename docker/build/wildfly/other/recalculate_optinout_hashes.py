# -*- coding: utf-8 -*-
"""
Created on Tue Apr 20 14:44:29 2021

@author: akombeiz
"""

import os
import sys
import sqlalchemy as db
import hashlib
import base64
import re
import traceback
import xml.etree.ElementTree as ET


def get_datasource_element_from_xml(name_jndi):
    """
    Iterates recursively through all deployed xmls in wildfly deployments folder
    and searches for xml with given jndi-name

    Parameters
    ----------
    name_jndi : str
        jndi-name of datasource to search

    Raises
    ------
    SystemExit
        When datasource for given jdni-name could not be found

    Returns
    -------
    element : xml element
        Root node of found datasource

    """
    for filename in os.listdir(PATH_WILDFLY_DEPLOYMENTS):
        if filename.endswith('.xml.deployed'):
            filename = os.path.splitext(filename)[0]
            path_file = os.path.join(PATH_WILDFLY_DEPLOYMENTS, filename)
            xml = ET.parse(path_file)
            for element in xml.iter():
                for key_attr in element.attrib.keys():
                    if key_attr == 'jndi-name' and element.attrib['jndi-name'] == name_jndi:
                        return element
    raise SystemExit('xml of datasource could not be found')


def extract_connection_credentials_from_datasource(element):
    """
    Iterates through datasource node and extracts connection-url and credentials

    Parameters
    ----------
    element : xml element
        Node of datasource to extract credentials from

    Returns
    -------
    credentials : dict
        Dict with connection-url and extracted credentials

    """
    credentials = dict()
    for node in element:
        if ('connection-url' in node.tag):
            credentials['connection-url'] = node.text
        if ('security' in node.tag):
            for creds in node:
                if('user-name' in creds.tag):
                    credentials['user-name'] = creds.text
                if('password' in creds.tag):
                    credentials['password'] = creds.text
    return credentials


def check_and_update_outdated_pat_root(dict_creds):
    """
    Connects to i2b2crcdata.optinout_patients and searches for pat_ext where
    pat_root does not correspond to current patient.root in aktin.properties.
    Updates pat_root and recalculates pat_psn for found patients.

    Parameters
    ----------
    dict_creds : dict
        Dict with connection-url and credentials

    Returns
    -------
    None.

    """
    root = get_aktin_property('cda.patient.root.preset')
    try:
        engine = get_db_engine(dict_creds)
        with engine.connect() as connection:
            opt = db.Table('optinout_patients', db.MetaData(), autoload_with=engine)
            list_pat = get_patients_with_outdated_root(connection, opt, root)
            update_root_of_outdated_patients(connection, opt, list_pat, root)
    finally:
        engine.dispose()


def get_db_engine(dict_creds):
    """
    Extracts connection path (format: HOST:PORT/DB) out of given connection-url
    and creates engine object with given credentials to enable a database
    connection

    Parameters
    ----------
    dict_creds : dict
        Dict with connection-url and credentials.

    Returns
    -------
    sqlalchemy.engine
        Engine object which enables a connection with i2b2crcdata

    """
    pattern = 'jdbc:postgresql://(.*?)(\?searchPath=.*)?$'
    connection = re.search(pattern, dict_creds['connection-url']).group(1)
    return db.create_engine('postgresql+psycopg2://{0}:{1}@{2}'.format(dict_creds['user-name'], dict_creds['password'], connection))


def get_patients_with_outdated_root(connection, table_obs, root):
    """
    Select from optinout_patients all pat_ext for given study (input argument)
    where pat_root does not correspond to root in aktin.properties

    Parameters
    ----------
    connection : sqlalchemy.connection
        Connection object of engine to run querys on
    table_obs : sqlalchemy.Table
        Table object of i2b2crcdata.observation_fact
    root : str
        cda.patient.root.preset from aktin.properties

    Returns
    -------
    list_pat : list
        List with pat_ext where root does not correspond to aktin.properties root

    """
    list_pat = []
    query = db.select([table_obs.c['pat_ext']])\
        .where(db.and_(table_obs.c['study_id'] == ID_STUDY, table_obs.c['pat_root'] != root))
    result = connection.execution_options(stream_results=True).execute(query)
    while True:
        chunk = result.fetchone()
        if not chunk:
            break
        list_pat.append(chunk[0])
    return list_pat


def update_root_of_outdated_patients(connection, table_obs, list_pat, root):
    """
    Iterates through list of pat_ext with wrong root and updates pat_root and
    recalculates pat_psn in i2b2crcdata.optionout_patients

    Parameters
    ----------
    connection : sqlalchemy.connection
        Connection object of engine to run querys on
    table_obs : sqlalchemy.Table
        Table object of i2b2crcdata.observation_fact
    list_pat : list
        List with pat_ext where root does not correspond to aktin.properties root
    root : str
        cda.patient.root.preset from aktin.properties

    Raises
    ------
    SystemExit
        If error during update transaction

    Returns
    -------
    None.

    """
    alg = get_aktin_property('pseudonym.algorithm')
    salt = get_aktin_property('pseudonym.salt')
    for pat in list_pat:
        pat_psn = one_way_anonymizer(alg, root, pat, salt)
        statement = table_obs.update().where(db.and_(table_obs.c['study_id'] == ID_STUDY, table_obs.c['pat_ext'] == pat)).\
            values({
                'pat_root':root,
                'pat_psn':pat_psn,
            })
        transaction = connection.begin()
        try:
            connection.execute(statement)
            transaction.commit()
        except:
            transaction.rollback()
            traceback.print_exc()
            raise SystemExit('update operation failed')


def one_way_anonymizer(name_alg, root, extension, salt):
    """
    Hashes given patient id with given algorithm, root.preset and salt. If
    no algorithm was stated, sha1 is used

    Parameters
    ----------
    name_alg : str
        Name of cryptographic hash function from aktin.properties
    root : str
        Root preset from aktin.properties
    extension : str
        Patient id to hash
    salt : str
        Cryptographic salt from aktin.properties

    Returns
    -------
    str
        Hashed patient id

    """
    name_alg = convert_crypto_alg_name(name_alg) if name_alg else 'sha1'
    composite = '/'.join([str(root), str(extension)])
    composite = salt + composite if salt else composite
    buffer = composite.encode('UTF-8')
    alg = getattr(hashlib, name_alg)()
    alg.update(buffer)
    return base64.urlsafe_b64encode(alg.digest()).decode('UTF-8')


def convert_crypto_alg_name(name_alg):
    """
    Converts given name of java cryptograhpic hash function to python demanted
    format, example:
        MD5 -> md5
        SHA-1 -> sha1
        SHA-512/224 -> sha512_224

    Parameters
    ----------
    name_alg : str
        Name to convert to python format

    Returns
    -------
    str
        Converted name of hash function

    """
    return str.lower(name_alg.replace('-','',).replace('/','_'))


def get_aktin_property(property_aktin):
    """
    Searches aktin.properties for given key and returns the corresponding value

    Parameters
    ----------
    property_aktin : str
        Key of the requested property

    Returns
    -------
    str
        Corresponding value of requested key or empty string if not found

    """
    if not os.path.exists(PATH_AKTIN_PROPERTIES):
        raise SystemExit('file path for aktin.properties is not valid')
    with open(PATH_AKTIN_PROPERTIES) as properties:
        for line in properties:
            if '=' in line:
                key, value = line.split('=', 1)
                if(key == property_aktin):
                    return value.strip()
        return ''


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit("sys.argv don't match")

    ID_STUDY = sys.argv[1]
    PATH_AKTIN_PROPERTIES='/opt/wildfly/standalone/configuration/aktin.properties'
    PATH_WILDFLY_DEPLOYMENTS='/opt/wildfly/standalone/deployments'

    datasource = get_aktin_property('i2b2.datasource.crc')
    element_ds = get_datasource_element_from_xml(datasource)
    dict_creds = extract_connection_credentials_from_datasource(element_ds)
    check_and_update_outdated_pat_root(dict_creds)