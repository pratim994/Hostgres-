.PHONY: build up down status logs init-app failover benchmark workload report test validate clean clean-volumes

build:
	docker compose build

up:
	docker compose up -d --build

down:
	docker compose down

status:
	./scripts/cluster-status.sh

logs:
	docker compose logs -f pg1 pg2 pg3 etcd1 etcd2 etcd3 haproxy pgbouncer prometheus grafana

init-app:
	./scripts/init-app.sh

failover:
	./scripts/failover-test.sh

benchmark:
	./scripts/benchmark.sh

workload:
	python3 -m application.workload

report:
	python3 -m experiments.reporting

test:
	pytest -q tests/unit

validate:
	python3 -m compileall -q scripts experiments
	python3 -c 'import yaml; yaml.safe_load(open("docker-compose.yml")); yaml.safe_load(open("monitoring/prometheus.yml")); yaml.safe_load(open("monitoring/alerts.yml"))'
	docker compose config --quiet

clean:
	docker compose down

clean-volumes:
	./scripts/remove-volumes.sh
