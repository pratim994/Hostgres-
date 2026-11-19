FROM postgres:16-bookworm

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install --no-cache-dir --break-system-packages \
       'patroni[etcd3]==4.0.6' 'psycopg2-binary==2.9.10'

COPY config/patroni/ /etc/patroni/
COPY scripts/render-patroni-config.py /usr/local/bin/render-patroni-config.py
COPY scripts/patroni-entrypoint.sh /usr/local/bin/patroni-entrypoint.sh
RUN chown -R postgres:postgres /etc/patroni \
    && chmod 755 /etc/patroni \
    && chmod 755 /usr/local/bin/render-patroni-config.py \
    && chmod 755 /usr/local/bin/patroni-entrypoint.sh

USER root
EXPOSE 5432 8008
ENTRYPOINT ["/usr/local/bin/patroni-entrypoint.sh"]
CMD ["patroni", "/run/patroni.yml"]
