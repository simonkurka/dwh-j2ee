FROM php:apache
RUN apt-get update && apt-get install -y wget unzip
RUN wget -qO /tmp/i2b2-webclient.zip https://github.com/i2b2/i2b2-webclient/archive/v1.7.12a.0002.zip
RUN unzip -qd /var/www/html/ /tmp/i2b2-webclient.zip
RUN rm /tmp/i2b2-webclient.zip
RUN mv /var/www/html/i2b2-webclient-* /var/www/html/webclient
RUN sed -i 's|name: \"HarvardDemo\",|name: \"AKTIN\",|' /var/www/html/webclient/i2b2_config_data.js
RUN sed -i 's|urlCellPM: \"http://services.i2b2.org/i2b2/services/PMService/\",|urlCellPM: \"http://127.0.0.1:9090/i2b2/services/PMService/\",|' /var/www/html/webclient/i2b2_config_data.js
RUN sed -i 's|loginDefaultUsername : \"demo\"|loginDefaultUsername : \"\"|' /var/www/html/webclient/js-i2b2/i2b2_ui_config.js
RUN sed -i 's|loginDefaultPassword : \"demouser\"|loginDefaultPassword : \"\"|' /var/www/html/webclient/js-i2b2/i2b2_ui_config.js
COPY ./aktin-j2ee-reverse-proxy.conf /etc/apache2/conf-available/aktin-j2ee-reverse-proxy.conf
RUN a2enmod proxy_http
RUN a2enconf aktin-j2ee-reverse-proxy
VOLUME /var/log/apache2

