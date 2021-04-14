from chillapi.abc import AuditLogHandler, AuditLog


class MyAuditHandler(AuditLogHandler):
    def __init__(self, name: str):
        self.name = name

    def log(self, log: AuditLog):
        print(self.__dict__)
        print(log.__dict__)
        print(f'AUDIT SHOWS: {log.message}')
