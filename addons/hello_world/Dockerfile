ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

WORKDIR /usr/src/app

# Copy data for add-on
COPY run.sh flask_hello_world.py ./

# Install requirements for add-on
RUN chmod a+x run.sh
RUN apk add --no-cache python3 py-pip git && pip install --no-cache flask gunicorn

CMD [ "./run.sh" ]
