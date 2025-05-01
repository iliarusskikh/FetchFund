![domain:innovation-lab](https://img.shields.io/badge/innovation--lab-3D8BD3)
![domain:fetchfund](https://img.shields.io/badge/fetchfund-3D23DD)
![tag:fetchfund](https://img.shields.io/badge/fetchfund-4648A3)
![domain:research](https://img.shields.io/badge/research-3D23AD)

# Agent Description
Role: Gathers recent cryptocurrency news.
Workflow:
Awaits requests from the Main Agent.
Fetches news from the NewsAPI for the past 2 days.
Returns the news to the Main Agent.
Due to API restrictions only past day news are being fetched.


### EXAMPLE 1: CHAT PROTOCOL USER INPUT:
```
"trump"
```
### EXAMPLE 1: CHAT PROTOCOL OUTPUT:
```
[{"title":"Trump reportedly complained to Bezos about Amazon’s tariff plan","description":"President Donald Trump called Amazon founder Jeff Bezos to complain after a Punchbowl News report suggested the online marketplace planned on displaying the cost of tariffs next to product prices. White House officials told CNN that Trump called Bezos “shortl…"},{"title":"A turnaround victory made possible by Trump","description":"Mark Carney's party pull off an election win that once looked near-impossible, until the US president targeted Canada."},{"title":"Take It Down Act heads to Trump’s desk","description":"The Take It Down Act is heading to President Donald Trump’s desk after the House voted 409-2 to pass the bill, which will require social media companies to take down content flagged as nonconsensual (including AI-generated) sexual images. Trump has pledged to…"},{"title":"Why Carney's Liberals won - and the Conservatives lost","description":"The "Trump effect" helps a political newcomer deliver a stunning victory while his rivals made gains but still fell short."},{"title":"Apple’s Second-Biggest Supplier Says to Expect Empty Shelves Due to Trump Tariffs","description":"Pegatron says the uncertainty makes it hard to make contingency plans."},{"title":"‘Did I Miss Something?’: Online Shoppers Shocked as Trump Tariffs Jack Up Prices 145%","description":"Temu and Shein customers are facing high prices and dwindling choices."},{"title":"White House Panics After Report Claims Amazon Will Display Tariff Prices","description":""This is a hostile and political act by Amazon,” the White House Press Secretary said."},{"title":"Sarah Smith: Trump's breakneck start is fraught with political risk","description":"After 100 days of action and noise, there are dangers to the administration's shock-and-awe approach."}]

```

### USER INPUT MODEL:
```

class CryptonewsRequest(Model):
    limit: Optional[int] = 1
    keywords: str = Field(
        description="keywords separated with OR word"
    )

```
### OUTPUT MODEL:
```

class CryptonewsResponse(Model):
    response: str = Field(
        description="All found recent news based on keywords provided.",
    )

```
