# CEO Fixture Set

Each HTML file represents one crawled page. `labels.json` maps the filename to the expected CEO, founder, owner, president, managing director, or proprietor name.

Use `null` when the page should not produce a CEO candidate. Replace these starter placeholders with real saved team, leadership, and about pages as you build the labeled set.

Example:

```json
{
  "team_acme.html": "Jane Doe",
  "about_no_people.html": null
}
```

The test suite computes precision as correct returned names divided by any returned names, and recall as correct returned names divided by non-null labels.
