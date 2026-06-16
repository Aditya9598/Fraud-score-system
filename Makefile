.PHONY: setup-api test-api test-worker test-scorer test e2e

setup-api:
	cd api && pip install -r requirements.txt

test-api:
	cd api && pytest -v

test-worker:
	cd worker && npm test

test-scorer:
	cd scorer && cargo test

test:
	$(MAKE) test-api
	$(MAKE) test-worker
	$(MAKE) test-scorer

e2e:
	./scripts/e2e.sh
