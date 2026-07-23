from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SecurityFinding:
    category: str
    severity: str
    source: str
    pattern: str
    message: str


@dataclass(frozen=True)
class SecurityDecision:
    allowed: bool
    risk_level: str
    findings: list[SecurityFinding] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "risk_level": self.risk_level,
            "findings": [finding.__dict__ for finding in self.findings],
            "warnings": self.warnings,
        }


AGENT_CAPABILITIES: dict[str, dict[str, set[str]]] = {
    "PlanningAgent": {
        "allowed_actions": {"plan_workflow", "select_prompt_version"},
        "blocked_actions": {"read_secret", "send_email", "call_mcp", "approve_draft"},
    },
    "DocumentParserAgent": {
        "allowed_actions": {"read_staged_document", "parse_document"},
        "blocked_actions": {"read_external_file", "call_mcp", "write_database_directly"},
    },
    "LLMPatternAgent": {
        "allowed_actions": {"suggest_template_schema", "classify_sections"},
        "blocked_actions": {"approve_template", "change_jurisdiction", "read_secret"},
    },
    "RetrievalAgent": {
        "allowed_actions": {"tenant_scoped_retrieval", "matter_scoped_retrieval"},
        "blocked_actions": {"cross_tenant_retrieval", "unrestricted_web_search"},
    },
    "GroundedDraftingAgent": {
        "allowed_actions": {"draft_from_approved_context"},
        "blocked_actions": {"send_email", "call_payment", "approve_draft", "read_secret"},
    },
    "LegalSourceVerifierAgent": {
        "allowed_actions": {"official_source_validation", "allowlisted_fetch"},
        "blocked_actions": {"non_official_fetch", "wrong_country_law"},
    },
    "CritiqueAgent": {
        "allowed_actions": {"critique_draft", "mark_review_needed"},
        "blocked_actions": {"hide_findings", "approve_draft"},
    },
    "RevisionAgent": {
        "allowed_actions": {"revise_draft_text"},
        "blocked_actions": {"remove_review_warning", "rewrite_locked_clause_silently"},
    },
    "HumanReviewAgent": {
        "allowed_actions": {"prepare_review_packet", "record_feedback"},
        "blocked_actions": {"auto_file_document", "bypass_lawyer_review"},
    },
    "ToolPolicyAgent": {
        "allowed_actions": {"allow_tool_call", "block_tool_call", "audit_tool_call"},
        "blocked_actions": {"execute_tool_without_policy"},
    },
}


PROMPT_INJECTION_PATTERNS: tuple[tuple[str, str, str], ...] = (
    (r"\bignore\s+(all\s+)?(previous|prior|above)\s+instructions\b", "high", "Instruction override attempt."),
    (r"\bdisregard\s+(the\s+)?(system|developer|previous)\s+(message|instructions)\b", "high", "System/developer instruction bypass attempt."),
    (r"\breveal\s+(the\s+)?(api\s*key|secret|system\s+prompt|developer\s+message)\b", "critical", "Secret or system prompt exfiltration attempt."),
    (r"\bprint\s+(the\s+)?(api\s*key|secret|system\s+prompt|developer\s+message)\b", "critical", "Secret or system prompt exfiltration attempt."),
    (r"\byou\s+are\s+now\s+(dan|developer\s+mode|unrestricted|jailbroken)\b", "high", "Jailbreak persona attempt."),
    (r"\bdisable\s+(safety|guardrails|policy|filters)\b", "high", "Safety bypass attempt."),
    (r"\bcall\s+(the\s+)?(tool|mcp|function)\b", "medium", "Untrusted content is attempting to invoke tools."),
    (r"\bsend\s+(this|the)\s+(draft|document|data)\s+to\s+", "high", "Untrusted content is attempting external transmission."),
    (r"\bdelete\s+(all|the)\s+(files|records|database|drafts)\b", "critical", "Destructive action request in untrusted content."),
    (r"\bmark\s+(this|the)\s+(draft|document)\s+as\s+(approved|lawyer-approved|final)\b", "high", "Attempt to bypass lawyer review."),
    (r"\buse\s+(us|uk|english|american)\s+law\s+instead\s+of\s+(german|de|selected)\s+law\b", "high", "Attempt to override selected jurisdiction."),
)


TOXICITY_PATTERNS: tuple[tuple[str, str, str], ...] = (
    (r"\bkill\s+(yourself|them|him|her)\b", "critical", "Violent or self-harm abusive instruction."),
    (r"\bthreaten\s+(the\s+)?(judge|opponent|witness|employee|employer)\b", "high", "Threatening language request."),
    (r"\bharass\s+(the\s+)?(judge|opponent|witness|employee|employer)\b", "high", "Harassment request."),
    (r"\bdeny\s+(service|representation|employment)\s+because\s+of\s+(race|religion|gender|nationality|disability|age)\b", "high", "Discriminatory instruction involving protected traits."),
)


UNSAFE_LEGAL_PATTERNS: tuple[tuple[str, str, str], ...] = (
    (r"\bguarantee\s+(we\s+will\s+win|success|the\s+outcome)\b", "medium", "Unsafe legal outcome guarantee."),
    (r"\bfile\s+(this|the)\s+(draft|document)\s+without\s+(lawyer|attorney|counsel)\s+review\b", "high", "Attempt to bypass legal review."),
    (r"\bfabricate\s+(evidence|facts|citations|witnesses)\b", "critical", "Request to fabricate legal material."),
    (r"\binvent\s+(a\s+)?(citation|case|statute|authority)\b", "critical", "Request to invent legal authority."),
)


BLOCKING_SEVERITIES = {"critical", "high"}
SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def assess_text_security(text: str, *, source: str) -> SecurityDecision:
    findings: list[SecurityFinding] = []
    for category, patterns in {
        "prompt_injection": PROMPT_INJECTION_PATTERNS,
        "toxicity_or_bias": TOXICITY_PATTERNS,
        "unsafe_legal_instruction": UNSAFE_LEGAL_PATTERNS,
    }.items():
        for pattern, severity, message in patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                findings.append(
                    SecurityFinding(
                        category=category,
                        severity=severity,
                        source=source,
                        pattern=pattern,
                        message=message,
                    )
                )
    return _decision_from_findings(findings)


def assess_generation_payload(*, doc_type: str, case_data: dict[str, Any], source_documents: list[Any] | None) -> SecurityDecision:
    findings: list[SecurityFinding] = []
    combined_case_text = "\n".join(f"{key}: {value}" for key, value in case_data.items())
    findings.extend(assess_text_security(doc_type, source="doc_type").findings)
    findings.extend(assess_text_security(combined_case_text, source="case_data").findings)
    for index, document in enumerate(source_documents or []):
        name = getattr(document, "name", "") if not isinstance(document, dict) else str(document.get("name", ""))
        content = getattr(document, "content", "") if not isinstance(document, dict) else str(document.get("content", ""))
        findings.extend(assess_text_security(name, source=f"source_documents[{index}].name").findings)
        findings.extend(assess_text_security(content, source=f"source_documents[{index}].content").findings)
    return _decision_from_findings(findings)


def assess_llm_output(text: str, *, source: str = "llm_output") -> SecurityDecision:
    return assess_text_security(text, source=source)


def evaluate_tool_policy(
    *,
    tool_name: str,
    payload: dict[str, Any],
    country: str,
    allowed_domains: list[str],
    actor_role: str = "",
) -> SecurityDecision:
    findings: list[SecurityFinding] = []
    normalized_tool = tool_name.lower()
    if any(term in normalized_tool for term in ["secret", "api_key", "credential", "password"]):
        findings.append(_finding("tool_policy", "critical", "tool_name", "Tool attempts to access secrets.", "secret_access"))
    if any(term in normalized_tool for term in ["payment", "billing", "email", "delete", "database_write"]):
        findings.append(_finding("tool_policy", "high", "tool_name", "Tool requires explicit backend service authorization.", "privileged_tool"))
    if actor_role in {"junior_lawyer", "paralegal"} and any(term in normalized_tool for term in ["admin", "firm_manage", "invite"]):
        findings.append(_finding("tool_policy", "high", "actor_role", "Junior/paralegal role cannot call firm admin tools.", "role_violation"))
    if "legal" in normalized_tool or "search" in normalized_tool:
        urls = [str(url) for url in payload.get("source_urls", [])]
        if not allowed_domains:
            findings.append(_finding("tool_policy", "high", "country", f"No official-source allowlist is configured for {country}.", "missing_allowlist"))
        for url in urls:
            host = host_from_url(url)
            if not any(host == domain or host.endswith(f".{domain}") for domain in allowed_domains):
                findings.append(_finding("tool_policy", "high", "source_urls", f"Non-official legal source rejected: {host}", "non_official_source"))
    text_payload = _payload_text(payload)
    findings.extend(assess_text_security(text_payload, source="tool_payload").findings)
    return _decision_from_findings(findings)


def agent_allows_action(agent_name: str, action: str) -> bool:
    capabilities = AGENT_CAPABILITIES.get(agent_name, {})
    return action in capabilities.get("allowed_actions", set()) and action not in capabilities.get("blocked_actions", set())


def host_from_url(url: str) -> str:
    value = url.strip().lower()
    value = value.removeprefix("https://").removeprefix("http://")
    return value.split("/", 1)[0].split(":", 1)[0]


def _payload_text(payload: dict[str, Any]) -> str:
    try:
        return str(payload)
    except Exception:
        return ""


def _decision_from_findings(findings: list[SecurityFinding]) -> SecurityDecision:
    if not findings:
        return SecurityDecision(allowed=True, risk_level="low", findings=[], warnings=[])
    max_severity = max(findings, key=lambda finding: SEVERITY_ORDER.get(finding.severity, 0)).severity
    allowed = not any(finding.severity in BLOCKING_SEVERITIES for finding in findings)
    warnings = sorted({finding.message for finding in findings if finding.severity == "medium"})
    return SecurityDecision(allowed=allowed, risk_level=max_severity, findings=findings, warnings=warnings)


def _finding(category: str, severity: str, source: str, message: str, pattern: str) -> SecurityFinding:
    return SecurityFinding(category=category, severity=severity, source=source, pattern=pattern, message=message)
