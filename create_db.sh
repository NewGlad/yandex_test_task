sql -c "ALTER USER postgres PASSWORD 'postgres';"
psql -c "CREATE DATABASE rest_db WITH OWNER postgres CONNECTION LIMIT -1;"
psql -c "CREATE DATABASE rest_db_test WITH OWNER postgres CONNECTION LIMIT -1;"
psql -d rest_db -f ./init_db.sql
psql -d rest_db_test -f ./init_db.sql