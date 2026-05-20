# Development Guide

This guide provides detailed information for developers working on the AI Travel Planner Agent project.

## Project Overview

The AI Travel Planner Agent is a Python CLI application that generates personalized travel itineraries using Google Vertex AI Gemini. The architecture is modular, designed for easy adaptation to web frontends (Streamlit, FastAPI, Next.js).

### Key Technologies
- **Python 3.11+**
- **Google Vertex AI** - Gemini text generation
- **OpenWeatherMap API** - Weather data (optional)
- **Google Maps API** - Places and routing (optional)

## Project Structure Deep Dive

### `project/config.py`
Central configuration registry. Loads all environment variables here:
- `GCP_PROJECT_ID`, `GCP_LOCATION` - Google Cloud setup
- `GEMINI_MODEL` - Currently "gemini-2.5-flash"
- API keys for weather and maps (optional)
- Memory file path
- Valid options for budget, interests, food types

**Extend when**: Adding new configuration or environment-dependent behavior.

### `project/exceptions.py`
Custom exception hierarchy:
- `TravelPlannerError` - Base exception
- `WeatherServiceError` - Weather API failures
- `MapsServiceError` - Maps API failures

**Extend when**: Adding new service integrations that need distinct error handling.

### `project/logging_config.py`
Centralized logging setup. Singleton pattern — `setup_logging()` is idempotent.

**Extend when**: Adding new loggers or changing log format/levels.

### Agent Layer

#### `project/agent/travel_agent.py`
**Orchestrator** — the heart of the application. Responsibilities:
1. Loads user preferences and memory
2. Calls `weather_service` to get current conditions
3. Calls `maps_service` for attractions and distances
4. Runs `decision_engine` to build planning constraints
5. Optimizes visit order with `route_optimizer`
6. Calls `itinerary_service` to generate plans
7. Persists user memory

**Key method**: `generate_both_plans(user_input) → Dict[str, str]`

**Extend when**: Adding new data sources (e.g., flight prices, hotel ratings) or new planning constraints.

#### `project/agent/cli_planner.py`
**Interactive CLI loop**. Handles:
- User input prompts (destination, days, budget, interests)
- Preference summary and confirmation
- Plan display
- Regeneration and session management

**Key function**: `run_planner()` - main entry point

**Extend when**: 
- Wrapping with Streamlit, FastAPI, or other UI framework
- Adding new prompt types or interactions

#### `project/agent/decision_engine.py`
**Rule-based planning** — NO LLM calls. Applies static rules to generate constraints.

Examples:
- If rain forecast: prefer indoor activities
- If budget="budget": minimize paid attractions
- If "adventure" interest: prioritize outdoor activities

Output: `PlanningDecision` object with flags and explanations (for LLM context).

**Extend when**: Adding new planning rules or adjusting existing heuristics.

### Services Layer

#### `project/services/gemini_service.py`
**Vertex AI client**. Minimal wrapper:
- Initializes Vertex AI once per process
- Handles authentication errors with clear messages
- Implements exponential backoff for quota errors
- Shows loading spinner during generation
- Generates text completions with configurable temperature/tokens

**Key function**: `generate_text_completion(prompt) → str`

**Note**: This module is intentionally domain-agnostic — use it for any text generation, not just travel.

**Extend when**: Supporting other Vertex AI models or adding streaming/structured output.

#### `project/services/itinerary_service.py`
**Travel plan orchestration**. Builds prompts and calls Gemini:
- `generate_travel_plan()` - Single plan (Budget or Premium)
- `generate_both_plans()` - Both plans with rate limiting

Uses either:
- Static prompt: `build_travel_prompt()` - legacy, simple
- Adaptive prompt: `build_adaptive_travel_prompt()` - with weather, routing, memory context

**Extend when**: 
- Adding new plan types (e.g., "Luxury", "Solo Traveler")
- Supporting structured output (JSON itineraries)
- Adding replanning or iterative refinement

#### `project/services/weather_service.py`
**OpenWeatherMap client**. Returns structured JSON:
- Current conditions (temperature, humidity, description)
- 24-hour precipitation forecast (max probability, rain signal)
- Location normalization

**Key function**: `fetch_weather_for_destination(destination_query) → Dict`

Graceful degradation: Returns empty dict if key is missing or API fails.

**Extend when**: 
- Adding historical weather patterns
- Supporting alerts (extreme conditions)
- Caching weather responses

#### `project/services/maps_service.py`
**Google Maps client**. Two main APIs:
- **Places Text Search**: Find attractions by query
- **Distance Matrix**: Get driving distances and times between locations

**Key functions**:
- `search_places(query) → List[Dict]` - Attractions
- `distance_matrix(origins, destinations) → Dict` - Routing data
- `fetch_route_data_for_attractions()` - Wrapped helper

Graceful degradation: Returns empty lists if key is missing or API fails.

**Extend when**: 
- Adding elevation API for hiking routes
- Supporting public transit estimates
- Caching distance matrices

### Models Layer

#### `project/models/user_input.py`
Simple dataclass:
```python
@dataclass
class UserInput:
    destination: str
    travel_days: int
    budget_type: str  # "budget" | "medium" | "premium"
    interests: List[str]  # ["adventure", "food", "nature", ...]
    preferred_food_type: Optional[str]  # "local", "vegetarian", ...
```

**Convert to Pydantic** when exposing via FastAPI/REST API.

#### `project/models/planning_context.py`
Two main classes:

**`PlanningDecision`** - Output of `decision_engine.build_planning_decision()`:
```python
@dataclass
class PlanningDecision:
    prefer_indoor: bool
    avoid_beaches: bool
    prioritize_outdoor_activities: bool
    tags: List[str]  # ["rain_mode", "budget_mode", "adventure_outdoor", ...]
    explanations: List[str]  # ["Museum and indoor-friendly stops preferred due to rain..."]
```

**`AdaptivePlanContext`** - Everything the prompt needs:
- Weather data
- Planning decision
- Attractions and routing
- User memory snapshot
- Explainability notes

**Extend when**: Adding new planning dimensions (e.g., accessibility, carbon footprint).

### Utils Layer

#### `project/utils/formatter.py`
Terminal styling and display:
- Color codes (CYAN, GREEN, RED, etc.)
- Structured print functions: `print_banner()`, `print_section_header()`, `print_itinerary()`, etc.
- Text wrapping for terminal readability

**Extend when**: Changing terminal UI or output format.

#### `project/utils/route_optimizer.py`
Greedy TSP solver (nearest-neighbor heuristic). Given attractions and distances, returns:
- Optimized visit order
- Total distance
- Total duration

**Why not exact TSP?** For typical itineraries (5-10 attractions), nearest-neighbor is fast and good enough. Exact solvers are overkill.

**Extend when**: Supporting advanced optimization (e.g., time-window constraints, cost minimization).

### Memory Layer

#### `project/memory/user_memory.py`
JSON-based persistence. Stores user preferences across sessions:
```python
@dataclass
class UserMemoryState:
    preferred_budget: Optional[str]
    travel_interests: List[str]
    preferred_food_type: Optional[str]
    past_destinations: List[str]  # Last 25
```

Automatically loaded/saved by `TravelAgent`.

**Extend when**: 
- Adding database support
- Storing trip history or feedback
- Implementing recommendations based on past trips

#### `project/memory/store.py`
Abstract protocol for session memory (not yet implemented). Placeholder for future trip/session-level data.

### Prompts Layer

#### `project/prompts/itinerary_prompt.py`
Prompt engineering. Two builders:

1. **Static prompt** — Simple, explicit instructions:
   ```python
   build_travel_prompt(user_input, plan_type)
   ```
   Good for: Simple use cases, easy to debug.

2. **Adaptive prompt** — Injects weather, routing, memory, decision tags:
   ```python
   build_adaptive_travel_prompt(user_input, plan_type, context)
   ```
   Good for: Better itineraries, explains why certain activities are suggested.

**Pattern**: Embed JSON context in prompt for Gemini to reference.

**Extend when**:
- A/B testing different prompt phrasings
- Adding few-shot examples
- Supporting structured output generation

### Entry Points

#### `main.py`
Thin wrapper:
1. Adds repo root to `sys.path`
2. Calls `setup_logging()`
3. Calls `run_planner()`

#### `weather_test_cli.py`
Standalone test for OpenWeatherMap. Useful for:
- Debugging weather API issues
- Verifying API key
- Testing destination name resolution

## Development Workflow

### Adding a New Service

Example: Adding flight price service.

1. **Create** `project/services/flight_service.py`:
   ```python
   def fetch_flight_prices(origin, destination, date):
       # Call API, return structured JSON
       pass
   ```

2. **Add exception** to `project/exceptions.py`:
   ```python
   class FlightServiceError(TravelPlannerError):
       pass
   ```

3. **Configure** in `project/config.py`:
   ```python
   FLIGHT_API_KEY = os.environ.get("FLIGHT_API_KEY")
   FLIGHT_API_TIMEOUT = float(os.environ.get("FLIGHT_API_TIMEOUT", "15"))
   ```

4. **Integrate** in `project/agent/travel_agent.py`:
   ```python
   flights = flight_service.fetch_flight_prices(...)
   # Add to AdaptivePlanContext
   ```

5. **Update prompts** to reference flight data.

6. **Test locally**:
   ```bash
   export FLIGHT_API_KEY="test-key"
   python main.py
   ```

### Adding a New Prompt Type

Example: Adding a "Solo Traveler" variant.

1. **Add to config**:
   ```python
   PLAN_TYPES = ["budget", "medium", "premium", "solo"]
   ```

2. **Add builder** to `project/prompts/itinerary_prompt.py`:
   ```python
   def build_solo_prompt(user_input, context=None):
       # Emphasize safety, social opportunities, budget
       pass
   ```

3. **Integrate** in `project/services/itinerary_service.py`:
   ```python
   elif plan_type == "solo":
       prompt = build_solo_prompt(user_input, context)
   ```

4. **Test in CLI**:
   ```python
   # Modify cli_planner.py to offer "solo" as an option
   ```

## Debugging Tips

### Enable Debug Logging
```bash
export LOG_LEVEL=DEBUG
python main.py
```

Logs go to stderr, showing:
- API calls (URLs, status codes)
- Memory file operations
- Decision engine reasoning
- Prompt text (truncated)

### Test Weather Service Independently
```bash
export OPENWEATHERMAP_API_KEY="your-key"
python weather_test_cli.py
```

### Test Maps Service
```python
from project.services import maps_service
places = maps_service.search_places("Eiffel Tower")
print(places)
```

### Inspect Generated Plans
Plans are markdown strings. After generation:
```python
for plan_type, content in plans.items():
    print(f"\n=== {plan_type} ===")
    print(content)
```

## Common Issues & Solutions

### Module Import Errors
**Problem**: `ModuleNotFoundError: No module named 'project'`

**Solution**: Ensure you're running from the repo root, and `main.py` has added it to `sys.path`.

### Vertex AI Auth Failures
**Problem**: `PERMISSION_DENIED` or `AUTHENTICATION_FAILED`

**Solution**:
```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### Rate Limiting
**Problem**: Gemini API returns 429 (quota exceeded)

**Solution**: The code retries with exponential backoff. Wait or increase quota in Cloud Console.

### Weather/Maps Unavailable
**Problem**: Plans generated without weather/routing context

**Solution**: This is intentional! The system degrades gracefully. Set the missing API keys to enable these features.

## Performance Considerations

1. **API Calls**: Typical flow makes ~5 API calls:
   - 1 × Weather
   - 1 × Places search
   - 1 × Distance matrix
   - 2 × Gemini (Budget + Premium)

2. **Caching Opportunities**:
   - Weather: Cache per destination for 1 hour
   - Places: Cache per query
   - Memory: Already cached in JSON file

3. **Parallelization**:
   - Budget and Premium generation could run in parallel
   - Weather and Maps could run in parallel
   (Current code is sequential for simplicity)

## Testing Strategy

### Unit Tests (Future)
- Decision engine rules
- Route optimizer output
- Formatter display logic

### Integration Tests (Future)
- Weather service with mock API
- Maps service with mock API
- End-to-end CLI flow

### Manual Testing (Current)
- Full CLI interaction
- Weather test CLI
- Different budget/interest combinations

## Deployment Considerations

### Docker
Would need a `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

### Cloud Run
Could wrap with FastAPI for serverless deployment:
```python
from fastapi import FastAPI
from project.agent.travel_agent import TravelAgent

app = FastAPI()

@app.post("/plan")
def plan(user_input: UserInput):
    agent = TravelAgent()
    return agent.generate_both_plans(user_input)
```

## Future Work

See [CHANGELOG.md](CHANGELOG.md) for roadmap.

Key areas:
- Web UI (Streamlit, Next.js)
- Database persistence
- Multi-user support
- Advanced filtering
- Booking integrations
- Real-time pricing

---

Questions? See [CONTRIBUTING.md](CONTRIBUTING.md) or open an issue.
