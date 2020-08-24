# Pull base image
FROM python:3.6-slim

# Install psql so that "python manage.py dbshell" works. install so we can pull dynamic-rest package from github.
RUN apt-get -y update && apt-get install -y postgresql-client git

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
#	--no-interaction: not to ask any interactive questions
# 	--no-ansi: flag to make your output more log friendly
COPY poetry.lock pyproject.toml /app/
RUN pip install --no-cache-dir --upgrade pip \
	&& pip install --no-cache-dir poetry==1.0.5 \
	&& poetry config virtualenvs.create false \
 	&& poetry install --no-interaction --no-ansi \
 	&& pip uninstall --yes poetry \
 	&& rm -rf ~/.config/pypoetry

# Copy project
COPY . /app/
