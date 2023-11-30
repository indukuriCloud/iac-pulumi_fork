gc:
	( \
		gcloud auth application-default login; \
		GOOGLE_CREDENTIALS="$(HOME)/.config/gcloud/application_default_credentials.json" export GOOGLE_CREDENTIALS; \
	)