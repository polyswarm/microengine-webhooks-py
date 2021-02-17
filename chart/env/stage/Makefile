RELEASE_NAME=microengine-webhooks-py
CHARTS_DIR=../../.
YAML_FILES=$(CHARTS_DIR)/values.yaml $(CHARTS_DIR)/secrets.yaml secrets.yaml values.yaml
HELM_VERSION=helm3

deployment-delete:
		kubectl delete deployments/$(RELEASE_NAME)

restart: deployment-delete upgrade

lint: $(YAML_FILES)
		$(HELM_VERSION) lint $(CHARTS_DIR) $(addprefix -f ,  $(YAML_FILES))

template: $(YAML_FILES)
		$(HELM_VERSION) template $(RELEASE_NAME) $(CHARTS_DIR)  $(addprefix -f ,  $(YAML_FILES))

upgrade: $(YAML_FILES)
		$(HELM_VERSION) upgrade $(RELEASE_NAME) $(CHARTS_DIR) $(addprefix -f ,  $(YAML_FILES))

install: $(YAML_FILES)
		$(HELM_VERSION) install $(RELEASE_NAME) $(CHARTS_DIR) $(addprefix -f ,  $(YAML_FILES))

.PHONY: deployment-delete restart upgrade install lint template
