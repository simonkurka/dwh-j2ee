#!/bin/bash
set -e
VERSION=$1
BUILDDIR=aktin-dwh_$VERSION

cp -r ./DEBIAN ./$BUILDDIR/DEBIAN

#
# Download i2b2 webclient
#
wget https://github.com/i2b2/i2b2-webclient/archive/v1.7.12a.0002.zip -P /tmp
unzip /tmp/v1.7.12a.0002.zip -d ./$BUILDDIR/var/www/html
mv ./$BUILDDIR/var/www/html ./$BUILDDIR/var/www/html/webclient

sed -i 's|name: \"HarvardDemo\",|name: \"AKTIN\",|' ./$BUILDDIR/var/www/html/webclient/i2b2_config_data.js
sed -i 's|urlCellPM: \"http://services.i2b2.org/i2b2/services/PMService/\",|urlCellPM: \"http://127.0.0.1:9090/i2b2/services/PMService/\",|' ./$BUILDDIR/var/www/html/webclient/i2b2_config_data.js
sed -i 's|loginDefaultUsername : \"demo\"|loginDefaultUsername : \"\"|' ./$BUILDDIR/var/www/html/webclient/js-i2b2/i2b2_ui_config.js
sed -i 's|loginDefaultPassword : \"demouser\"|loginDefaultPassword : \"\"|' ./$BUILDDIR/var/www/html/webclient/js-i2b2/i2b2_ui_config.js

#
# Create apache2 proxy configuration
#
mkdir -p ./$BUILDDIR/etc/apache2/conf-available
cat > ./$BUILDDIR/etc/apache2/conf-available/aktin-j2ee-reverse-proxy.conf <<EOF
ProxyPreserveHost On
ProxyPass /aktin http://localhost:9090/aktin
ProxyPassReverse /aktin http://localhost:9090/aktin
EOF


#
# Download wildfly
#
wget https://download.jboss.org/wildfly/18.0.0.Final/wildfly-18.0.0.Final.zip -P /tmp
unzip /tmp/wildfly-$WILDFLY_VERSION.zip -d ./$BUILDDIR/opt
mv ./$BUILDDIR/opt/wildfly-* ./$BUILDDIR/opt/wildfly

mkdir -p ./$BUILDDIR/lib/systemd/system ./$BUILDDIR/var/lib/aktin ./$BUILDDIR/etc/wildfly
cp ./$BUILDDIR/opt/wildfly/docs/contrib/scripts/systemd/wildfly.service ./$BUILDDIR/lib/systemd/system/
cp ./$BUILDDIR/opt/wildfly/docs/contrib/scripts/systemd/wildfly.conf ./$BUILDDIR/etc/wildfly/
cp ./$BUILDDIR/opt/wildfly/docs/contrib/scripts/systemd/launch.sh ./$BUILDDIR/opt/wildfly/bin/

echo JBOSS_HOME=\"/opt/wildfly\" >> ./$BUILDDIR/etc/wildfly/wildfly.conf
echo JBOSS_OPTS=\"-Djboss.http.port=9090 -Djrmboss.as.management.blocking.timeout=6000\" >> ./$BUILDDIR/etc/wildfly/wildfly.conf

sed -i 's/-Xms64m -Xmx512m/-Xms1024m -Xmx2g/' ./$BUILDDIR/opt/wildfly/bin/appclient.conf
sed -i 's/-Xms64m -Xmx512m/-Xms1014m -Xmx2g/' ./$BUILDDIR/opt/wildfly/bin/standalone.conf
sed -i 's|<rotate-size value="50m"/>|<rotate-size value="1g"/>|' ./$BUILDDIR/opt/wildfly/bin/standalone.conf

patch -p3 -d ./$BUILDDIR/opt/wildfly < ./standalone.xml.patch

wget https://www.aktin.org/software/repo/org/i2b2/1.7.12a/i2b2.war -P ./$BUILDDIR/opt/wildfly/standalone/deployments/
wget https://jdbc.postgresql.org/download/postgresql-42.2.8.jar -P ./$BUILDDIR/opt/wildfly/standalone/deployments/

cp ./xml/* ./$BUILDDIR/opt/wildfly/standalone/deployments/
cp ./aktin.properties ./$BUILDDIR/opt/wildfly/standalone/configuration/

cp ./dwh-j2ee-*.ear ./$BUILDDIR/opt/wildfly/standalone/deployments/

dpkg-deb --build $BUILDDIR


