from fastapi import HTTPException
from server.rdtsserver.db.tables import AssemblyCreate
from server.rdtsserver.db.tables import CrystalCreate


def validate_string(value: str, object_error: str) -> str:
    value = value.strip()
    if not value:
        raise HTTPException(status_code=400, detail=f"{object_error} must not be empty!")
    return value


def validate_positive_number(number: int, object_error: str):
    if number < 0:
        raise HTTPException(status_code=400, detail=f"{object_error} must be positive!")


def validate_AssemblyCreate(assembly: AssemblyCreate) -> AssemblyCreate:
    assembly.name = validate_string(value=assembly.name, object_error="Assembly name")
    for i in range(len(assembly.crystals)):
        assembly.crystals[i] = validate_string(value=assembly.crystals[i], object_error="Crystal name")
    return assembly


def validate_CrystalCreate(crystal: CrystalCreate) -> CrystalCreate:
    crystal.name = validate_string(value=crystal.name, object_error="Crystal name")
    crystal.assembly_name = validate_string(value=crystal.assembly_name, object_error="Assembly name")
    validate_positive_number(crystal.place, object_error="Place")
    return crystal
