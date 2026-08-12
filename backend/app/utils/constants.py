import enum

class Role(enum.Enum):
    REPORTER = "reporter"
    SUPPORT_ENGINEER = "support_engineer"
    TEAM_LEAD = "team_lead"
    ADMIN = "admin"

    @classmethod
    def values(cls):
        return [item.value for item in cls]

class PriorityCode(enum.Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"

    @classmethod
    def values(cls):
        return [item.value for item in cls]

class ImpactLevel(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @classmethod
    def values(cls):
        return [item.value for item in cls]

class UrgencyLevel(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @classmethod
    def values(cls):
        return [item.value for item in cls]

class IncidentStatus(enum.Enum):
    NEW = "new"
    TRIAGE = "triage"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    RESOLVED = "resolved"
    REOPENED = "reopened"
    CLOSED = "closed"

    @classmethod
    def values(cls):
        return [item.value for item in cls]

class ResolutionCode(enum.Enum):
    FIXED = "fixed"
    WORKAROUND = "workaround"
    NOT_A_BUG = "not_a_bug"
    DUPLICATE = "duplicate"
    CANT_REPRODUCE = "cant_reproduce"
    THIRD_PARTY = "third_party"

    @classmethod
    def values(cls):
        return [item.value for item in cls]

class CriticalityLevel(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def values(cls):
        return [item.value for item in cls]