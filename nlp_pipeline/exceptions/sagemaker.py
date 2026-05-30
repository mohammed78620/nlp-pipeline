class EndpointDoesNotExistError(Exception):
    def __init__(self, endpoint):
        self.message = f"Endpoint {endpoint} does not exist"
        super().__init__(self.message)
