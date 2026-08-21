FROM python:3.13-alpine
RUN addgroup -S -g 10001 lab && adduser -S -D -H -u 10001 -G lab lab \
 && pip install --no-cache-dir --disable-pip-version-check pyftpdlib==2.0.1
COPY server.py /opt/lab/server.py
COPY fixture.txt /srv/ftp/fixture.txt
RUN chown -R 10001:10001 /srv/ftp /opt/lab
USER 10001:10001
WORKDIR /opt/lab
EXPOSE 21
ENTRYPOINT ["python", "server.py"]
