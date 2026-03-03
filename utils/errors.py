class UnAuthorizedUserException(Exception):
    """Excepción lanzada cuando el usuario no está autorizado para usar el servicio."""
    
    def __init__(self, phone: str):
        self.phone = phone
        super().__init__(f"Usuario {phone} no autorizado.")

class AIProccesingException(Exception):
    """Excepción lanzada cuando el servicio de IA falla."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(f"Mensaje {message} no se puede procesar.")