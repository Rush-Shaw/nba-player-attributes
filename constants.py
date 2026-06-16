from pathlib import Path

from pydantic import BaseModel


DATA_PATH = Path(__file__).parent / "data" / "processed"

class PlayerAttributes(BaseModel):
    overallAttribute: float
    closeShot: float
    midRangeShot: float
    threePointShot: float
    freeThrow: float
    shotIQ: float
    offensiveConsistency: float
    layup: float
    standingDunk: float
    drivingDunk: float
    postHook: float
    postFade: float
    postControl: float
    drawFoul: float
    hands: float
    interiorDefense: float
    perimeterDefense: float
    steal: float
    block: float
    helpDefenseIQ: float
    passPerception: float
    defensiveConsistency: float
    speed: float
    strength: float
    vertical: float
    stamina: float
    hustle: float
    overallDurability: float
    passAccuracy: float
    ballHandle: float
    speedWithBall: float
    passIQ: float
    passVision: float
    offensiveRebound: float
    defensiveRebound: float
    agility: float
    name: str
    season: int
    team: str
    position_group: str
    height_inches: int
    weight_lbs: int

class PaginatedResponse(BaseModel):
    total: int
    limit: int
    offset: int
    data: list[PlayerAttributes]