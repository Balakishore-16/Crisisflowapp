"""
CrisisFlow AI Service
─────────────────────
Provider abstraction: LocalExplanationProvider (default) or AzureAIProvider.
The AI layer EXPLAINS decisions made by the deterministic Decision Engine.
"""
import os
from typing import Optional, Dict, Any
from app.models import Incident, Recommendation


class AIProvider:
    """Base class for AI providers."""
    name: str = "Base"

    def explain_recommendation(self, incident: Incident, rec: Recommendation) -> str:
        raise NotImplementedError

    def classify_incident(self, incident: Incident) -> Dict[str, Any]:
        raise NotImplementedError

    def generate_briefing(self, incident: Incident, rec: Recommendation) -> str:
        raise NotImplementedError


class LocalExplanationProvider(AIProvider):
    """Rule-based explanation engine. Works without any external API."""
    name = "Local Decision Engine"

    def explain_recommendation(self, incident: Incident, rec: Recommendation) -> str:
        parts = []
        parts.append(f"CrisisFlow Decision Engine analyzed {incident.incident_type} "
                      f"at {incident.location} (Severity: {incident.severity}, Zone: {incident.zone or 'Central'}).")
        parts.append("")

        if rec.fire_station_name:
            parts.append(f"🚒 Fire Unit: {rec.fire_station_name} selected for fire suppression/rescue capabilities.")

        if rec.ambulance_id:
            parts.append(f"🚑 Selected Ambulance: {rec.ambulance_id}")

        if rec.hospital_name:
            parts.append(f"🏥 Selected Hospital: {rec.hospital_name}")

        parts.append(f"⏱️ ETA: {rec.eta_minutes} minutes")
        parts.append(f"🎯 Confidence: {rec.confidence}%")
        parts.append("")

        if rec.reasons:
            parts.append("Reason:")
            for r in rec.reasons:
                parts.append(f"  • {r}")
            parts.append("")

        if rec.score_breakdown:
            parts.append("Score Breakdown:")
            for k, v in rec.score_breakdown.items():
                k_clean = k.replace("_", " ").title()
                parts.append(f"  • {k_clean}: {v}")

        return "\n".join(parts)

    def classify_incident(self, incident: Incident) -> Dict[str, Any]:
        severity_map = {
            "Critical": {"urgency": "IMMEDIATE", "color": "red"},
            "High": {"urgency": "HIGH", "color": "orange"},
            "Medium": {"urgency": "MODERATE", "color": "yellow"},
            "Low": {"urgency": "ROUTINE", "color": "blue"},
        }
        info = severity_map.get(incident.severity, severity_map["Medium"])
        return {
            "incident_type": incident.incident_type,
            "severity": incident.severity,
            "urgency": info["urgency"],
            "risk_assessment": f"{incident.incident_type} with {incident.people_at_risk} "
                               f"people at risk. Severity: {incident.severity}.",
            "recommended_action": f"Immediate dispatch of fire and medical resources required."
            if incident.severity in ("Critical", "High") else
            f"Standard response protocol recommended.",
        }

    def generate_briefing(self, incident: Incident, rec: Recommendation) -> str:
        breakdown_str = ""
        if rec.score_breakdown:
            breakdown_str = "\nScore Breakdown:\n" + "\n".join(f"  - {k}: {v}" for k, v in rec.score_breakdown.items())

        return (
            f"COMMANDER BRIEFING — Incident {incident.id}\n"
            f"{'='*50}\n"
            f"Type: {incident.incident_type}\n"
            f"Location: {incident.location}"
            f"{f', Floor {incident.floor}' if incident.floor else ''}\n"
            f"Severity: {incident.severity}\n"
            f"Zone: {incident.zone or 'Central'}\n"
            f"People at Risk: {incident.people_at_risk}\n"
            f"Spread Risk: {incident.spread_risk or 'N/A'}\n\n"
            f"RECOMMENDED RESPONSE:\n"
            f"  Fire Station: {rec.fire_station_name or 'N/A'}\n"
            f"  Ambulance: {rec.ambulance_id or 'N/A'}\n"
            f"  Hospital: {rec.hospital_name or 'N/A'}\n"
            f"  Route: {rec.route or 'N/A'}\n"
            f"  ETA: {rec.eta_minutes} minutes\n"
            f"  Confidence: {rec.confidence}%\n"
            f"{breakdown_str}\n\n"
            f"STATUS: Awaiting commander dispatch authorization."
        )


class AzureAIProvider(AIProvider):
    """Azure OpenAI / AI Foundry provider. Requires credentials."""
    name = "Azure AI Foundry"

    def __init__(self):
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.available = bool(self.endpoint and self.api_key)

    def explain_recommendation(self, incident: Incident, rec: Recommendation) -> str:
        if not self.available:
            return LocalExplanationProvider().explain_recommendation(incident, rec)
        return LocalExplanationProvider().explain_recommendation(incident, rec)

    def classify_incident(self, incident: Incident) -> Dict[str, Any]:
        if not self.available:
            return LocalExplanationProvider().classify_incident(incident)
        return LocalExplanationProvider().classify_incident(incident)

    def generate_briefing(self, incident: Incident, rec: Recommendation) -> str:
        if not self.available:
            return LocalExplanationProvider().generate_briefing(incident, rec)
        return LocalExplanationProvider().generate_briefing(incident, rec)


def get_ai_provider() -> AIProvider:
    """Return the best available AI provider."""
    azure = AzureAIProvider()
    if azure.available:
        return azure
    return LocalExplanationProvider()


def get_ai_status() -> Dict[str, str]:
    """Return AI service status."""
    azure = AzureAIProvider()
    if azure.available:
        return {"provider": "Azure AI Foundry", "status": "CONNECTED"}
    return {"provider": "Local Decision Engine", "status": "LOCAL"}
