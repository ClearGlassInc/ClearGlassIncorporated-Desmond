FROM node:22-alpine
RUN addgroup -S -g 10001 lab && adduser -S -D -H -u 10001 -G lab lab
WORKDIR /app
COPY server.mjs .
USER 10001:10001
EXPOSE 8080
CMD ["node", "server.mjs"]
