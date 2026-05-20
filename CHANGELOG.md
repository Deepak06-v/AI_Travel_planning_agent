# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-05-20

### Added
- Initial release of AI Travel Planner Agent
- Vertex AI Gemini integration for itinerary generation
- Budget and Premium travel plan generation
- OpenWeatherMap integration for adaptive weather-aware planning
- Google Maps integration for route optimization and attraction search
- JSON-based user memory for session persistence
- Rule-based decision engine for deterministic planning constraints
- Interactive CLI with color formatting and spinners
- Terminal UI with sectioned display of itineraries
- Support for multiple user interests: adventure, food, nature, shopping, culture
- Configurable budget tiers: budget, medium, premium
- Food preference options: any, local, vegetarian, vegan, halal, seafood, street_food
- Comprehensive error handling and graceful degradation
- Full documentation and setup instructions
- Example .env configuration template
- Multi-option regeneration and trip replanning

### Under the Hood
- Modular architecture for easy frontend integration
- Separated data models, services, and CLI layers
- Type hints throughout for better IDE support
- Structured logging with configurable levels
- TSP-based greedy route optimizer for attraction visit order
- Prompt engineering with adaptive context injection
- Exponential backoff for API quota rate limiting

### Known Limitations
- One user at a time (single-session CLI)
- JSON memory storage only (no database)
- Weather and Maps APIs are optional but recommended
- Tested primarily on Python 3.11+

## Future Roadmap

### [1.1.0] - Planned
- Streamlit web UI
- FastAPI backend for headless operation
- Multi-day regeneration with temporal anchoring
- Itinerary comparison (Budget vs Premium)
- Export to PDF / iCalendar formats

### [2.0.0] - Planned
- Database persistence (PostgreSQL)
- Multi-user support with authentication
- Advanced filtering by activity duration, cost, accessibility
- Integration with booking APIs (flights, hotels, activities)
- Real-time pricing updates
- Social itinerary sharing
