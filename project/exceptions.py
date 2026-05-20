"""Domain-specific errors for external integrations and orchestration."""


class TravelPlannerError(Exception):
    """Base error for the travel planner application."""


class WeatherServiceError(TravelPlannerError):
    """OpenWeatherMap or weather pipeline failures."""


class MapsServiceError(TravelPlannerError):
    """Google Maps API failures."""
