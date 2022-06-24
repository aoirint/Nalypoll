# nalypoll

## Prepare

Copy `template.env`, `template.env.django`, `template.env.mysql` to `.env`, `.env.django`, `.env.mysql` and set values.

```shell
docker-compose -f docker-compose.dev.yml up -d

docker-compose -f docker-compose.dev.yml exec app python3 manage.py migrate
docker-compose -f docker-compose.dev.yml exec app python3 manage.py collectstatic
```

## Deploy

Copy `docker-compose.yml`, `default.conf.template` and `.env*` to a new directory and set values.

### Execute

```shell
docker-compose up -d

docker-compose exec app python3 manage.py migrate
docker-compose exec app python3 manage.py collectstatic
```