# recipe-restful-api
Recipe Sharing Platform API

The API only works on local MSSQL Server Database Engines and other database engines (sqlite), provided the parameters are set properly.

To download: 'git clone repo'

Setup local MSSQL Server, set parameters in app.py ('param'), then run in bash: 'python app.py'

You may also run 'docker compose up -d', docker-compose.yaml already handles building both the MSSQL server and the API.


Notes:
* MSSQL Server and API are Containerized properly in Docker, but work independently of each other.
* Files that may be deemed irrelevant are done in an attempt to get the bonus part of the test.
* Reason for Failure: Was not able to create a workaround for app.py's sqlalchemy.create_all() in time.
* This was done under a time constraint, alternative approaches may be done if given the opportunity.

