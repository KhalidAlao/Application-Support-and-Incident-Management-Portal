import enum

class Role(enum.Enum):
    REPORTER = "Reporter"
    SUPPORT_ENGINEER = "Support Engineer"
    TEAM_LEAD = "Team Lead"
    ADMIN = "Admin"

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
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

    @classmethod
    def values(cls):
        return [item.value for item in cls]

class UrgencyLevel(enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

    @classmethod
    def values(cls):
        return [item.value for item in cls]

class IncidentStatus(enum.Enum):
    NEW = "New"
    TRIAGE = "Triage"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    ON_HOLD = "On hold"
    RESOLVED = "Resolved"
    REOPENED = "Reopened"
    CLOSED = "Closed"

    @classmethod
    def values(cls):
        return [item.value for item in cls]

class ResolutionCode(enum.Enum):
    FIXED = "Fixed"
    WORKAROUND = "Workaround"
    NOT_A_BUG = "Not A Bug"
    DUPLICATE = "Duplicate"
    CANT_REPRODUCE = "Can't Reproduce"
    THIRD_PARTY = "Third Party"

    @classmethod
    def values(cls):
        return [item.value for item in cls]

class CriticalityLevel(enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

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