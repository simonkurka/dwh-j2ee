Software package for deployment of the data warehouse
=====================================================

Building
--------
To build the dwh-j2ee module, the following other modules
must be previously built: dwh-api, dwh-db, dwh-import, dwh-query, 
broker, dwh-admin.

This can be done automatically, by running `mvn -f dwh.xml clean install`
in the parent project.

Manual deployment
-----------------
For manual deployment of the EAR bundle, the
following steps must be performed.

1. A working i2b2 installation is required

2. Database and users for AKTIN needs to be created:
```
# as user postgres
createdb aktin
psql -c "CREATE ROLE aktin with password 'aktin'" aktin
psql -c "CREATE SCHEMA IF NOT EXISTS  aktin AUTHORIZATION aktin" aktin
psql -c "GRANT ALL ON SCHEMA aktin to aktin" aktin
psql -c "ALTER ROLE "aktin" WITH LOGIN" aktin
```

3. Add datasource configuration to wildfly:
```
# as root in wildfly/bin
jboss-cli.sh --connect
# enter the following commands
# if the data source already exists, remove first: data-source remove --name=AktinDS
set jdbcUrl=jdbc:postgresql://localhost:5432/aktin
set username=aktin
set password=aktin
set driver=postgresql-9.2-1002.jdbc4.jar
set module=com.postgresql
set resource=/home/jboss/Downloads/postgresql-9.2-1002.jdbc4.jar
set name=AktinDS
set jndiname=java:jboss/datasources/AktinDS
data-source add --name=$name --jndi-name=$jndiname --driver-name=$driver --jta=false --connection-url=$jdbcUrl --user-name=$username --password=$password
```

4. Add email configuration to wildfly
```
TODO (can be done later)
```

5. Add AKTIN configuration parameters: 
Create a file `/opt/wildfly*/standalone/configuration/aktin.properties`
```
local.cn=Zentrale Notaufnahme Entenhausen
local.o=Klinik Entenhausen
local.ou=Notaufnahme
local.l=Entenhausen
local.s=Entenstaat
local.c=Entenland
local.email=admin@klinik-entenhausen.el
local.tz=Europe/Berlin
rscript.binary=/usr/bin/Rscript
# needed for read/write access to the i2b2 database
i2b2.project=AKTIN
i2b2.datasource.crc=java:/QueryToolDemoDS
# needed for i2b2 authentication and user management
i2b2.service.pm=http://localhost:8080/i2b2/services/PMService/
# TODO create dir /var/lib/aktin and chown to wildfly
report.data.path=/var/lib/aktin/reports
report.temp.path=/var/tmp/report-temp
report.archive.path=/var/lib/aktin/report-archive
broker.data.path=/var/lib/aktin/broker
broker.archive.path=/var/lib/aktin/broker-archive
broker.uris=http://localhost:8080/lalal
db.datasource=java:jboss/datasources/AktinDS
email.session=java:jboss/mail/AktinMailSession
wildfly.management.url=http://localhost:19990/management
wildfly.management.user=admin
wildfly.management.password=admin2
```

6. Undeploy previous bundle and deploy new bundle
```
cd /opt/wildfly*/standalone/deployments
rm dwh-j2ee-*.ear.deployed
# wait for dwh-j2ee-*.ear.undeployed to appear
# to prevent hanging of wildfly, stop and restart
service wildfly stop
cp NEW_EAR ./
service wildfly start
```