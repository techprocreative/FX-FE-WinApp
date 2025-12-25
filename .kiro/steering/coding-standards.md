# Coding Standards & Best Practices

## PyQt6 UI Development

### Architecture Patterns
- **MVP/MVVM Pattern**: Separate presentation logic from business logic
- **Component-based Design**: Reusable UI components in `ui/components/`
- **Signal-Slot Pattern**: Use Qt's signal-slot mechanism for loose coupling
- **Model-View Architecture**: Use QAbstractListModel/QAbstractTableModel for data display

### UI Best Practices
```python
# ✅ Good: Proper component initialization
class TradingCard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        # UI setup code
        pass
    
    def _connect_signals(self):
        # Signal connections
        pass

# ✅ Good: Use proper layouts
layout = QVBoxLayout()
layout.setContentsMargins(16, 16, 16, 16)
layout.setSpacing(12)

# ✅ Good: High-DPI support
app.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)
```

### Styling Guidelines
- Use consistent color scheme from `design_system.py`
- Implement dark/light theme support
- Use CSS-like stylesheets for consistent appearance
- Support high-DPI displays with proper scaling

## FastAPI Backend Development

### API Structure
```python
# ✅ Good: Proper async endpoint structure
@app.post("/api/v1/trades", response_model=TradeResponse)
async def create_trade(
    trade_data: TradeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    # Validate input
    # Process immediately needed data
    # Queue background tasks
    background_tasks.add_task(log_trade_activity, trade_data.id)
    return response

# ✅ Good: Background task implementation
def log_trade_activity(trade_id: str):
    try:
        with open("trade_log.txt", "a") as log_file:
            log_file.write(f"{datetime.now()}: Trade {trade_id} executed\n")
    except Exception as e:
        logger.error(f"Failed to log trade activity: {e}")
```

### Background Tasks Best Practices
- Use `BackgroundTasks` for quick operations (< 30 seconds)
- Implement proper error handling in background tasks
- Log all background task activities
- Use dependency injection for database sessions
- Clean up resources properly in finally blocks

### Error Handling
```python
# ✅ Good: Comprehensive error handling
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation failed", "errors": exc.errors()}
    )
```

## Machine Learning Integration

### Model Management
- Store models in organized directory structure by asset type
- Use encrypted model files for production
- Implement model versioning and rollback capabilities
- Validate model inputs before prediction

### Security Practices
```python
# ✅ Good: Secure model loading
def load_encrypted_model(model_path: str, key: bytes):
    try:
        with open(model_path, 'rb') as f:
            encrypted_data = f.read()
        decrypted_data = decrypt_data(encrypted_data, key)
        return joblib.loads(decrypted_data)
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise ModelLoadError(f"Cannot load model from {model_path}")
```

## Database Operations

### Supabase Integration
- Use connection pooling for better performance
- Implement retry logic for network failures
- Use transactions for multi-step operations
- Validate data before database operations

### Data Synchronization
```python
# ✅ Good: Robust sync implementation
async def sync_trade_data(trade_data: dict):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await supabase.table('trades').insert(trade_data).execute()
            logger.info(f"Trade data synced successfully: {response.data}")
            return response
        except Exception as e:
            logger.warning(f"Sync attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

## Testing Standards

### Property-Based Testing
- Use Hypothesis for generating test data
- Test edge cases and boundary conditions
- Validate invariants across different inputs

### Test Organization
```python
# ✅ Good: Structured test classes
class TestTradingEngine:
    @pytest.fixture
    def trading_engine(self):
        return TradingEngine(test_config)
    
    @given(st.floats(min_value=0.01, max_value=1000.0))
    def test_position_sizing(self, trading_engine, lot_size):
        # Property-based test implementation
        pass
    
    async def test_trade_execution_integration(self, trading_engine):
        # Integration test implementation
        pass
```

## Performance Guidelines

### Async Operations
- Use `asyncio.gather()` for concurrent operations
- Implement proper timeout handling
- Use connection pooling for external APIs
- Cache frequently accessed data

### Memory Management
- Clean up Qt objects properly
- Use weak references where appropriate
- Monitor memory usage in long-running operations
- Implement proper resource cleanup in exception handlers

## Logging Standards

### Structured Logging
```python
# ✅ Good: Structured logging with context
logger.info(
    "Trade executed",
    extra={
        "trade_id": trade.id,
        "symbol": trade.symbol,
        "volume": trade.volume,
        "price": trade.price,
        "user_id": user.id
    }
)
```

### Log Levels
- **DEBUG**: Detailed diagnostic information
- **INFO**: General operational messages
- **WARNING**: Recoverable errors or unexpected conditions
- **ERROR**: Serious problems that need attention
- **CRITICAL**: System-threatening errors

## Security Requirements

### API Security
- Validate all input data
- Use proper authentication and authorization
- Implement rate limiting
- Sanitize user inputs
- Use HTTPS for all communications

### Data Protection
- Encrypt sensitive data at rest
- Use secure key management
- Implement proper session management
- Log security-related events