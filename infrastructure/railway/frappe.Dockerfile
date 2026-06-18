FROM frappe/bench:latest

USER root
RUN apt-get update \
  && apt-get install -y --no-install-recommends curl mariadb-client \
  && rm -rf /var/lib/apt/lists/* \
  && mkdir -p /workspace/frappe-bench \
  && chown -R frappe:frappe /workspace/frappe-bench

USER frappe
WORKDIR /workspace/BEDO-ERP

COPY --chown=frappe:frappe . /workspace/BEDO-ERP

ENV FRAPPE_BENCH_PATH=/workspace/frappe-bench
ENV BEDO_APP_NAME=bedo_platform
ENV BEDO_APP_PATH=/workspace/BEDO-ERP/apps/bedo_platform
ENV UV_LINK_MODE=copy

RUN bench init --ignore-exist --skip-redis-config-generation --frappe-branch version-15 /workspace/frappe-bench \
  && ln -s /workspace/BEDO-ERP/apps/bedo_platform /workspace/frappe-bench/apps/bedo_platform \
  && cd /workspace/frappe-bench \
  && bench pip install --no-deps -e apps/bedo_platform \
  && if ! grep -qx "bedo_platform" sites/apps.txt; then printf "bedo_platform\n" >> sites/apps.txt; fi

CMD ["bash", "infrastructure/railway/start-web.sh"]
