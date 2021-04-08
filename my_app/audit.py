from chillapi.extensions.audit import AuditLog, AuditLogHandler


class MyAuditHandler(AuditLogHandler):
    def __init__(self, name: str):
        self.name = name

    def log(self, audit_log: AuditLog):
        print(self.name)
        print(f'AUDIT SHOWS: {audit_log.message}')
