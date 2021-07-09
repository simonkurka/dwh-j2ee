FROM postgres:12
COPY ./sql /docker-entrypoint-initdb.d
ENV POSTGRES_PASSWORD=postgres
VOLUME /var/log/postgres
VOLUME /var/lib/postgres/data

