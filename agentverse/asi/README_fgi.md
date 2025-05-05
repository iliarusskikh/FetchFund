![domain:innovation-lab](https://img.shields.io/badge/innovation--lab-3D8BD3)
![domain:fetchfund](https://img.shields.io/badge/fetchfund-3D23DD)
![tag:fetchfund](https://img.shields.io/badge/fetchfund-4648A3)
![domain:research](https://img.shields.io/badge/research-3D23AD)

# Agent Description
#### Role: 
Retrieves the Fear & Greed Index.

#### Workflow:
Awaits requests from the Main Agent.
Fetches the current Fear & Greed Index from CoinMarketCap.
Returns it to the Main Agent.


### EXAMPLE 1: CHAT PROTOCOL USER INPUT:
```
[Any]
```
### EXAMPLE 1: CHAT PROTOCOL OUTPUT:
```
data=[FearGreedData(value=55.0, value_classification='Neutral', timestamp='1746144000')] status='success' timestamp='2025-05-03T19:25:08.437663+00:00'
```

### USER INPUT MODEL:
```

class FGIRequest(Model):
    limit: Optional[int] = 1

```
### OUTPUT MODEL:
```

class FearGreedData(Model):
    value: float
    value_classification: str
    timestamp: str
    
class FGIResponse(Model):
    data: list[FearGreedData]
    status: str
    timestamp: str

```
