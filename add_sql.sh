psql $DATABASE_URL -f sql/clean.sql
psql $DATABASE_URL -f sql/schema.sql
psql $DATABASE_URL -f sql/modules.sql
psql $DATABASE_URL -f sql/users.sql
psql $DATABASE_URL -f sql/administrators.sql
psql $DATABASE_URL -f sql/tutors.sql
psql $DATABASE_URL -f sql/tutees.sql
psql $DATABASE_URL -f sql/offers.sql