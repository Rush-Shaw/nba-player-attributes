from pydantic import BaseModel


class PlayerAttributes(BaseModel):
    overallAttribute: float | None
    closeShot: float | None
    midRangeShot: float | None
    threePointShot: float | None
    freeThrow: float | None
    shotIQ: float | None
    offensiveConsistency: float | None
    layup: float | None
    standingDunk: float | None
    drivingDunk: float | None
    postHook: float | None
    postFade: float | None
    postControl: float | None
    drawFoul: float | None
    hands: float | None
    interiorDefense: float | None
    perimeterDefense: float | None
    steal: float | None
    block: float | None
    helpDefenseIQ: float | None
    passPerception: float | None
    defensiveConsistency: float | None
    speed: float | None
    strength: float | None
    vertical: float | None
    stamina: float | None
    hustle: float | None
    overallDurability: float | None
    passAccuracy: float | None
    ballHandle: float | None
    speedWithBall: float | None
    passIQ: float | None
    passVision: float | None
    offensiveRebound: float | None
    defensiveRebound: float | None
    agility: float | None
    name: str | None
    season: int | None
    team: str | None
    position_group: str | None
    height_inches: int | None
    weight_lbs: int | None


class PaginatedResponse(BaseModel):
    total: int
    limit: int
    offset: int
    data: list[PlayerAttributes]
