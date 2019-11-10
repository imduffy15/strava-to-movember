FROM python:3.6-slim-buster

ENV PIP_NO_CACHE_DIR "true"

WORKDIR /

RUN pip install --upgrade pip

COPY Pipfile.lock /
COPY pipenv-install.py /

RUN /pipenv-install.py && \
    rm -fr /usr/local/lib/python3.6/site-packages/pip && \
    rm -fr /usr/local/lib/python3.6/site-packages/setuptools

FROM python:3.6-slim-buster

ARG VERSION=dev

COPY --from=0 /usr/local/lib/python3.6/site-packages /usr/local/lib/python3.6/site-packages
COPY strava_to_movember /strava_to_movember

RUN sed -i "s/^__version__ = .*/__version__ = \"${VERSION}\"/" /strava_to_movember/__init__.py

ENTRYPOINT ["python", "-m", "strava_to_movember"]
