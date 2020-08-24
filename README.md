
# Collab-Backend

### Quick Start
* Have docker running. Install docker from here if necessary: https://docs.docker.com/docker-for-mac/install/
* Run:
    ```sh
    $ make up
    ```
    * This will download/build all required images, run migrations, and start the django server. Available at `localhost:8000`.

### Adding a python dependency
Everything runs inside docker, but we use `poetry` to manage our python dependencies.

* Install poetry: https://python-poetry.org/docs/#installation

To add a package, make sure you have all the packages already, by running
```sh
$ poetry install
```
then
```sh
$ poetry add <PACKAGE_NAME>
```
then rebuild the backend container
```sh
make rebuild-collab-backend-web
```

### Other Commands & Info
To spin up dependencies only (postgres, redis, etc.)
```sh
make deps-up
```

Then, in another terminal window, run the command you want:
* `make start` start the django server
* `make shell` start the django shell
* `make migrations` create migrations (if applicable)
* `make migrate` run migrations

Quick docker tips:
*   **Debugging application code**: 
    * Make sure the `collab_backend_web` is already running.
    * Insert the `pdb` statements where needed.
    * Then, in another terminal, run `docker attach collab_backend_web`. Pdb will work in this container.
* **Debugging 3rd party libs**: Sometimes you will want to inspect or debug 3rd party packages. 
    * Make sure the `collab_backend_web` is already running.
    * Run `docker exec -it collab_backend_web sh`
    * Inside that container, find the location of the package you want. Say you want to debug the `django` library. Run:
        ```sh
        # pip show django
        >> Location: /usr/local/lib/python3.6/site-packages
        # cd /usr/local/lib/python3.6/site-packages
        ```
    * Exit out of the container. Now, copy the file from container to host using `docker cp`. Note, you should run this from the root of the collab-backend.
        ```sh
        $ docker cp collab_backend_web:/usr/local/lib/python3.6/site-packages/django .
        ```
    * Now add logging or pdb to the django package.
* **Shell into the psql command-line client**: There are multiple ways to do so:
    * Easiest: run `make dbshell`
    * Alternatively, get the env-vars from `.env.dev`, and do:
        * `docker exec -it collab-backend_db_1 sh`
        * (Now in the db container): `psql -d <POSTGRES_DB> -U <POSTGRES_USER> -p <POSTGRES_PORT>` and then enter the `<POSTGRES_PASSWORD>` when prompted.
    * Alternatively, we are mapping the port on your host (5432) to the conatiner's port (5432). Therefore, is you have the psql client locally, you can just do:
        * `psql -h localhost -p 5432 -d <POSTGRES_DB> -U <POSTGRES_USER>` and then enter the `<POSTGRES_PASSWORD>` when prompted.
