from pydantic import BaseModel

class LoginIn(BaseModel):
    codigo_empleado: str | None = None
    email: str | None = None
    password: str

class AsesorOut(BaseModel):
    id: str
    codigo_empleado: str | None = None
    email: str | None = None
    nombres: str
    apellidos: str
    full_name: str = ""
    perfil: str
    rol: str = ""
    agencia_id: str | None = None

    def __init__(self, **data):
        super().__init__(**data)
        if not self.full_name:
            self.full_name = f"{self.nombres} {self.apellidos}".strip()

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    asesor: AsesorOut

    class Config:
        # Permitir que Pydantic convierta el modelo anidado
        pass
