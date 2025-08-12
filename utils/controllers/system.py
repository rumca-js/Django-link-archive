from ..sqlmodel import ConfigurationEntry

class ConfigurationEntryController(object):
    def __init__(self, db, session=None):
        self.conn = db
        self.session = session

    def get_session(self):
        if not self.session:
            return self.conn.get_session()
        else:
            return self.session

    def get(self):
        Session = self.get_session()
        with Session() as session:
            return session.query(ConfigurationEntry).first()

    def add(self, config):
        # Get the set of column names from EntriesTable
        valid_columns = {column.name for column in ConfigurationEntry.__table__.columns}

        # Remove keys that are not in EntriesTable
        config = {key: value for key, value in config.items() if key in valid_columns}

        config_obj = ConfigurationEntry(**config)

        Session = self.get_session()
        with Session() as session:
            session.add(config_obj)
            session.commit()
