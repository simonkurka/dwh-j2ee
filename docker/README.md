# AKTIN installer dockerized
## Use it
```sh
docker-compose up
```

## Build it
```sh
cd ..
mvn clean install
cp target/dwh-j2ee-*.ear docker/build/wildfly/
cd docker
docker-compose build
```
