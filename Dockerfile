# Pull base image
FROM python:3.7-slim

# Install psql so that "python manage.py dbshell" works. install so we can pull dynamic-rest package from github.
RUN apt-get -y update && apt-get install -y postgresql-client git

# install dependencies for playwright
# https://github.com/microsoft/playwright/blob/master/docs/docker/Dockerfile.bionic
# 2. Install WebKit dependencies
RUN apt-get update && apt-get install -y \
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
    libnotify4 \
    libxslt1.1 \
    libevent-2.1-6 \
    libgles2 \
    libvpx5 \
    libxcomposite1 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libepoxy0 \
    libgtk-3-0 \
    libharfbuzz-icu0 \
    libcups2

# 3. Install gstreamer and plugins to support video playback in WebKit.
RUN apt-get update && apt-get install -y \
    libgstreamer-gl1.0-0 \
    libgstreamer-plugins-bad1.0-0 \
    gstreamer1.0-plugins-good \
    gstreamer1.0-libav

# 4. Install Chromium dependencies
RUN apt-get update && apt-get install -y \
    libnss3 \
    libxss1 \
    libasound2 \
    fonts-noto-color-emoji \
    libxtst6

# 5. Install Firefox dependencies
RUN apt-get update && apt-get install -y \
    libdbus-glib-1-2 \
    libxt6

# 6. Install ffmpeg to bring in audio and video codecs necessary for playing videos in Firefox.
RUN apt-get update && apt-get install -y \
    ffmpeg

# 7. (Optional) Install XVFB if there's a need to run browsers in headful mode
RUN apt-get update && apt-get install -y \
    xvfb

# 8, 9, & 10: Is this needed? Taken from https://gist.github.com/mxschmitt/900aa310730bfac360717796b62ad072
# 8. For compiling libjpeg for WebKit
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    make

# 9. Compiling libjpeg for WebKit (for playwright)
RUN cd /tmp && \
    curl -s http://www.ijg.org/files/jpegsrc.v8d.tar.gz | tar zx && \
    cd jpeg-8d && \
    ./configure && \
    make && \
    make install

# 10. Add directory in which libjpeg was built to the search path
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# Needed for pyrcurl (which celery-sqs uses under the hood)
RUN apt-get install -y libcurl4-openssl-dev libssl-dev

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

# NON-root user. Better for security
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
