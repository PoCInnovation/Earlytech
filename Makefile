PY := python

.PHONY: db scrapp embedd clean save all status

db:
	$(PY) -m server_scrappe.cli db

scrapp:
	$(PY) -m server_scrappe.cli scrapp --limit 50

embedd:
	$(PY) -m server_scrappe.cli embedd --batch 200

clean:
	$(PY) -m server_scrappe.cli clean

save:
	$(PY) -m server_scrappe.cli save --out data/earlytech.db

status:
	$(PY) -m server_scrappe.cli status

all: db scrapp embedd save

dry-run-embedd:
	$(PY) -m server_scrappe.cli embedd --batch 200 --dry-run
