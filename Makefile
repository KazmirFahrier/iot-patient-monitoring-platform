run:
	uvicorn iot_monitoring.main:app --reload

test:
	pytest
