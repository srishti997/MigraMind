from alembic import context
from app.main import Base, engine
with engine.connect() as connection:
    sqlite = connection.dialect.name == 'sqlite'
    if sqlite:
        # Batch copies rebuild referenced tables. Validate references afterward.
        connection.exec_driver_sql('PRAGMA foreign_keys=OFF')
        connection.commit()
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction(): context.run_migrations()
    if sqlite:
        if connection.exec_driver_sql('PRAGMA foreign_key_check').fetchall():
            raise RuntimeError('Foreign-key validation failed; review the private database backup')
        connection.commit()
        connection.exec_driver_sql('PRAGMA foreign_keys=ON')
