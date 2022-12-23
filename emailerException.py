class ServiceNowAPIError(Exception):
    def __init__(self, *args: object) -> None:
        if args:
            self.message = args[0]
        else:
            self.message = "Error in Service Now API!"
        super().__init__(*args)

    def __str__(self) -> str:
        return self.message
class CreateEmailBodyError(Exception):
    def __init__(self, *args: object) -> None:
        if args:
            self.message = args[0]
        else:
            self.message = "Error creating email body!"
        super().__init__(*args)

    def __str__(self) -> str:
        return self.message
class SendSMTPEmailError(Exception):
    def __init__(self, *args: object) -> None:
        if args:
            self.message = args[0]
        else:
            self.message = "Error sending SMTP email!"
        super().__init__(*args)

    def __str__(self) -> str:
        return self.message