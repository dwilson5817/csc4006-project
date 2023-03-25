FROM perl:5

ENV CLOC_VERSION 1.96
ENV CLOC_SHA256 6eb34ab04798bf8053d32e5ee24acb201861bb74

RUN set -ex \
    && curl -sSL -o /usr/local/bin/cloc https://github.com/AlDanial/cloc/releases/download/v$CLOC_VERSION/cloc-$CLOC_VERSION.pl \
    && echo "${CLOC_SHA256}  /usr/local/bin/cloc" | shasum -c - \
    && chmod 755 /usr/local/bin/cloc

RUN apt-get update && apt-get install -y rsync \
    && rm -rf /var/lib/apt/lists/*

CMD ["cloc"]