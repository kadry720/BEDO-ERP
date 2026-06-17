FROM frappe/bench:latest

USER root
RUN apt-get update \
  && apt-get install -y --no-install-recommends curl mariadb-client \
  && rm -rf /var/lib/apt/lists/*

USER frappe
WORKDIR /workspace/BEDO-ERP

COPY --chown=frappe:frappe . /workspace/BEDO-ERP

ENV FRAPPE_BENCH_PATH=/workspace/frappe-bench
ENV BEDO_APP_NAME=bedo_platform
ENV BEDO_APP_PATH=/workspace/BEDO-ERP/apps/bedo_platform

CMD ["bash", "infrastructure/railway/start-web.sh"]
