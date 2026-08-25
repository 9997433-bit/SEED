PYTHON ?= python3
DATA_INDEX := game/data_build/units_index.json

.PHONY: help setup validate-data validate-data-strict check-data-index clean-data-index

help:
	@echo "make setup                 安装数据校验依赖（PyYAML / jsonschema）"
	@echo "make validate-data         校验 data/ 并刷新 $(DATA_INDEX)"
	@echo "make validate-data-strict  同上，但 Warning 也视为失败"
	@echo "make check-data-index      校验构建产物是否与数据一致（CI 用）"

setup:
	$(PYTHON) -m pip install -r tools/data_validator/requirements.txt

validate-data:
	$(PYTHON) tools/data_validator/validate.py --emit-index $(DATA_INDEX)

validate-data-strict:
	$(PYTHON) tools/data_validator/validate.py --strict --emit-index $(DATA_INDEX)

check-data-index:
	$(PYTHON) tools/data_validator/validate.py --check-index $(DATA_INDEX)

clean-data-index:
	rm -f $(DATA_INDEX)
