from chillapi.abc import AuditLogHandler, AuditLog


class MyAuditHandler(AuditLogHandler):
    def __init__(self, name: str):
        self.name = name

    def log(self, log: AuditLog):
        print(self.name)
        print(f'AUDIT SHOWS: {log.message}')
