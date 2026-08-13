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
    
STATUS_TRANSITIONS = {
    IncidentStatus.NEW.value: {
        IncidentStatus.TRIAGE.value,
        IncidentStatus.ON_HOLD.value,
        IncidentStatus.CLOSED.value,  # immediate close (admin only)
    },
    IncidentStatus.TRIAGE.value: {
        IncidentStatus.ASSIGNED.value,
        IncidentStatus.ON_HOLD.value,
        IncidentStatus.RESOLVED.value,
        IncidentStatus.CLOSED.value,
    },
    IncidentStatus.ASSIGNED.value: {
        IncidentStatus.IN_PROGRESS.value,
        IncidentStatus.ON_HOLD.value,
        IncidentStatus.RESOLVED.value,
        IncidentStatus.CLOSED.value,
    },
    IncidentStatus.IN_PROGRESS.value: {
        IncidentStatus.ON_HOLD.value,
        IncidentStatus.RESOLVED.value,
        IncidentStatus.CLOSED.value,
    },
    IncidentStatus.ON_HOLD.value: {
        IncidentStatus.IN_PROGRESS.value,
        IncidentStatus.ASSIGNED.value,
        IncidentStatus.RESOLVED.value,
        IncidentStatus.CLOSED.value,
    },
    IncidentStatus.RESOLVED.value: {
        IncidentStatus.CLOSED.value,
        IncidentStatus.REOPENED.value,
    },
    IncidentStatus.REOPENED.value: {
        IncidentStatus.IN_PROGRESS.value,
        IncidentStatus.ON_HOLD.value,
        IncidentStatus.RESOLVED.value,
        IncidentStatus.CLOSED.value,
    },
    IncidentStatus.CLOSED.value: {
        IncidentStatus.REOPENED.value,  # exceptional – only admin
    },
}

# Role restrictions for transitions.
# If a transition is not listed here, it is denied for everyone (fail-closed).
TRANSITION_ROLES = {
    (IncidentStatus.NEW.value, IncidentStatus.TRIAGE.value): {Role.SUPPORT_ENGINEER.value, Role.TEAM_LEAD.value, Role.ADMIN.value},
    (IncidentStatus.TRIAGE.value, IncidentStatus.ASSIGNED.value): {Role.SUPPORT_ENGINEER.value, Role.TEAM_LEAD.value, Role.ADMIN.value},
    (IncidentStatus.ASSIGNED.value, IncidentStatus.IN_PROGRESS.value): {Role.SUPPORT_ENGINEER.value, Role.TEAM_LEAD.value, Role.ADMIN.value},
    (IncidentStatus.ASSIGNED.value, IncidentStatus.ON_HOLD.value): {Role.SUPPORT_ENGINEER.value, Role.TEAM_LEAD.value, Role.ADMIN.value},  # <-- ADDED
    (IncidentStatus.IN_PROGRESS.value, IncidentStatus.ON_HOLD.value): {Role.SUPPORT_ENGINEER.value, Role.TEAM_LEAD.value, Role.ADMIN.value},
    (IncidentStatus.ON_HOLD.value, IncidentStatus.IN_PROGRESS.value): {Role.SUPPORT_ENGINEER.value, Role.TEAM_LEAD.value, Role.ADMIN.value},
    (IncidentStatus.IN_PROGRESS.value, IncidentStatus.RESOLVED.value): {Role.SUPPORT_ENGINEER.value, Role.TEAM_LEAD.value, Role.ADMIN.value},
    (IncidentStatus.RESOLVED.value, IncidentStatus.REOPENED.value): {Role.SUPPORT_ENGINEER.value, Role.TEAM_LEAD.value, Role.ADMIN.value},
    (IncidentStatus.REOPENED.value, IncidentStatus.IN_PROGRESS.value): {Role.SUPPORT_ENGINEER.value, Role.TEAM_LEAD.value, Role.ADMIN.value},
    (IncidentStatus.ON_HOLD.value, IncidentStatus.RESOLVED.value): {Role.SUPPORT_ENGINEER.value, Role.TEAM_LEAD.value, Role.ADMIN.value},  # <-- ADDED
    (IncidentStatus.ON_HOLD.value, IncidentStatus.CLOSED.value): {Role.TEAM_LEAD.value, Role.ADMIN.value},  # <-- ADDED (restricted)
    # Sensitive transitions
    (IncidentStatus.RESOLVED.value, IncidentStatus.CLOSED.value): {Role.TEAM_LEAD.value, Role.ADMIN.value},
    (IncidentStatus.CLOSED.value, IncidentStatus.REOPENED.value): {Role.ADMIN.value},
}

OPEN_STATUSES = [
    IncidentStatus.NEW.value,
    IncidentStatus.TRIAGE.value,
    IncidentStatus.ASSIGNED.value,
    IncidentStatus.IN_PROGRESS.value,
    IncidentStatus.ON_HOLD.value,
    IncidentStatus.REOPENED.value,
]

def get_allowed_roles_for_transition(from_status: str, to_status: str) -> set:
    """Return the set of roles allowed to perform this transition. Empty set = no one."""
    return TRANSITION_ROLES.get((from_status, to_status), set())

def is_transition_legal(from_status: str, to_status: str) -> bool:
    """Check if the transition is allowed by the state machine."""
    return to_status in STATUS_TRANSITIONS.get(from_status, set())