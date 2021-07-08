FROM jboss/wildfly:18.0.1.Final

USER root
RUN yum -y install wget

USER jboss
RUN sed -i 's/-Xms64m -Xmx512m/-Xms1024m -Xmx2g/' /opt/jboss/wildfly/bin/appclient.conf
RUN sed -i 's/-Xms64m -Xmx512m/-Xms1024m -Xmx2g/' /opt/jboss/wildfly/bin/standalone.conf

RUN sed -i 's|<rotate-size value=\"50m\"/>|<rotate-size value=\"1g\"/>|' /opt/jboss/wildfly/standalone/configuration/standalone.xml
RUN sed -i 's|<socket-binding name="http" port="${jboss.http.port:8080}"/>|<socket-binding name="http" port="${jboss.http.port:9090}"/>|' /opt/jboss/wildfly/standalone/configuration/standalone.xml

RUN wget -q https://www.aktin.org/software/repo/org/i2b2/1.7.12a/i2b2.war -P /opt/jboss/wildfly/standalone/deployments/
RUN wget -q https://jdbc.postgresql.org/download/postgresql-42.2.8.jar -P /opt/jboss/wildfly/standalone/deployments/

COPY ./xml/crc-ds.xml /opt/jboss/wildfly/standalone/deployments/crc-ds.xml
COPY ./xml/im-ds.xml /opt/jboss/wildfly/standalone/deployments/im-ds.xml
COPY ./xml/ont-ds.xml /opt/jboss/wildfly/standalone/deployments/ont-ds.xml
COPY ./xml/pm-ds.xml /opt/jboss/wildfly/standalone/deployments/pm-ds.xml
COPY ./xml/work-ds.xml /opt/jboss/wildfly/standalone/deployments/work-ds.xml

COPY ./jboss-cli /opt/jboss/jboss-cli
RUN /opt/jboss/jboss-cli/execute.sh

COPY ./dwh-j2ee-*.ear /opt/jboss/wildfly/standalone/deployments/
# aktin.properties is exposed via docker-compose
#COPY ./aktin.properties /opt/jboss/wildfly/standalone/configuration/aktin.properties

USER root
RUN mkdir -p /var/lib/aktin/import
RUN mkdir -p /var/lib/aktin/import-scripts
COPY ./import-scripts /var/lib/aktin/import-scripts
RUN chown -R jboss:jboss /var/lib/aktin

USER jboss

VOLUME /opt/jboss/wildfly/standalone/log
VOLUME /opt/jboss/wildfly/standalone/configuration/aktin.properties
VOLUME /var/lib/aktin

