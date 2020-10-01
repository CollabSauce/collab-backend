# Pull base image
FROM python:3.7-slim

# Install psql so that "python manage.py dbshell" works. install so we can pull dynamic-rest package from github.
RUN apt-get -y update && apt-get install -y postgresql-client git

# install dependencies for playwright
# https://gist.github.com/mxschmitt/900aa310730bfac360717796b62ad072
RUN apt-get update && \
    apt-get install -y \
    # WebKit dependencies
    libwoff1 \
    libopus0 \
    libwebp6 \
    libwebpdemux2 \
    libenchant1c2a \
    libgudev-1.0-0 \
    libsecret-1-0 \
    libhyphen0 \
    libgdk-pixbuf2.0-0 \
    libegl1 \
    libxslt1.1 \
    libgles2 \
    # gstreamer and plugins to support video playback in WebKit
    libgstreamer-gl1.0-0 \
    libgstreamer-plugins-bad1.0-0 \
    gstreamer1.0-plugins-good \
    # Chromium dependencies
    libnss3 \
    libxss1 \
    libasound2 \
    fonts-noto-color-emoji \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libxcomposite1 \
    libcups2 \
    libgtk-3-0 \
    # Firefox dependencies
    libdbus-glib-1-2 \
    libxt6 \
    # FFmpeg to bring in audio and video codecs necessary for playing videos in Firefox
    ffmpeg \
    # (Optional) XVFB if there's a need to run browsers in headful mode
    xvfb \
    # For compiling libjpeg for WebKit
    curl \
    gcc \
    make

# Compiling libjpeg for WebKit (for playwright)
RUN cd /tmp && \
    curl -s http://www.ijg.org/files/jpegsrc.v8d.tar.gz | tar zx && \
    cd jpeg-8d && \
    ./configure && \
    make && \
    make install

# Needed for pyrcurl (which celery-sqs uses under the hood)
RUN apt-get install -y libcurl4-openssl-dev libssl-dev

# Add directory in which libjpeg was built to the search path
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# install psycopg2 dependencies
# RUN apt-get install -y postgresql-dev gcc python3-dev musl-dev

# Set environment variables
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing pyc files to disc (equivalent to python -B option)
# PYTHONUNBUFFERED: Prevents Python from buffering stdout and stderr (equivalent to python -u option)
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
# note:
#   --no-interaction: not to ask any interactive questions
#   --no-ansi: flag to make your output more log friendly
COPY poetry.lock pyproject.toml /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir poetry==1.0.5 \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi \
    && pip uninstall --yes poetry \
    && rm -rf ~/.config/pypoetry

# NON-root user. mimics heroku
RUN useradd -m myuser
USER myuser

# more playwright
RUN python -m playwright install

# Copy project
COPY . /app/

# switch to root so we can set /app as `myuser` owner. Also switch to root so we can do the playwright cp hack below.
USER root
RUN chown -R myuser /app

# We get this issue when using playwright with celery. https://github.com/celery/celery/issues/928
# This hackily fixes the issue.
RUN cp collab_app/hack/playwright/main.py /usr/local/lib/python3.7/site-packages/playwright/main.py

# Switch back to myuser
USER myuser

# needed for heroku :/ . https://stackoverflow.com/a/62102995/9711626
# RUN python manage.py collectstatic --noinput
