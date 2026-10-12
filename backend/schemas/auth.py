"""Schemas Pydantic pour l'authentification et les profils utilisateurs."""
from typing import Optional
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=30, description="Identifiant de connexion")
    password: str = Field(..., min_length=6, max_length=128, description="Mot de passe")
    display_name: Optional[str] = Field(None, max_length=80, description="Nom affiche")
    phone: Optional[str] = Field(None, max_length=30, description="Telephone")
    region: Optional[str] = Field(None, max_length=80, description="Province / region du Burundi")
    crops: Optional[str] = Field(None, max_length=200, description="Cultures principales (separees par des virgules)")
    language: Optional[str] = Field("fr", max_length=5, description="Langue par defaut (fr, sw, en, rn)")


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=30)
    password: str = Field(..., min_length=1, max_length=128)


class ProfileUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=80)
    phone: Optional[str] = Field(None, max_length=30)
    region: Optional[str] = Field(None, max_length=80)
    crops: Optional[str] = Field(None, max_length=200)
    language: Optional[str] = Field(None, max_length=5)


class UserProfile(BaseModel):
    id: str
    username: str
    display_name: Optional[str] = None
    phone: Optional[str] = None
    region: Optional[str] = None
    crops: Optional[str] = None
    language: Optional[str] = "fr"
    created_at: Optional[str] = None


class AuthResponse(BaseModel):
    token: str
    user: UserProfile
    status: str = "success"
