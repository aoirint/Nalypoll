# nalypoll

**Twitter API有料化のため、[メンテナンスを終了しました](https://github.com/aoirint/nalypoll/issues/7)。**

Twitterの投票経過をグラフ化するWebアプリ（Django） / Twitter App for visualizing poll histories.

- <https://nalypoll.aoirint.com/>

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

## Add dependencies

Add the dependencies to `requirements.in` and execute below.

```shell
sudo apt install -y libmysqlclient-dev

# Python 3.11
pip3 install -U pip-tools

pip-compile
```

