Guides

/

Sharding

Last updated 3 months ago

## [link  to sharding](https://docs.api.cliniko.com/guides/sharding\#sharding) Sharding

Sharding is the term we use to define _regionally/geographically isolated instances_ of Cliniko. When new accounts sign up, they'll be able to choose the region in which their account data is hosted. Cliniko will then decide which shard within that region their account will live on.

### [link  to why-is-cliniko-sharded](https://docs.api.cliniko.com/guides/sharding\#why-is-cliniko-sharded) Why is Cliniko sharded?

1. Some jurisdictions require medical data to remain within the country/region
2. Lower end-user latency
3. Better performance and scalability

### [link  to how-does-this-impact-you](https://docs.api.cliniko.com/guides/sharding\#how-does-this-impact-you) How does this impact you?

All Cliniko accounts exist in a specific shard which contains all the data relevant to that account. The account must be accessed using a shard specific URL including the accounts unique Cliniko subdomain, eg `good-healthy-times.au3.cliniko.com`.

Trying to access a different shard with the account's subdomain will not work, eg `good-healthy-times.uk1.cliniko.com` will fail.

New users will be able to choose their region upon signing up to Cliniko. We will also make it possible to move a Cliniko account from one region to another on request. Any account that does move shards will need to access Cliniko with the new shard in their URL.

As the shard determines where an accounts data is stored it means that any integrator must know and use the shard when interacting with the Cliniko API. Using a shard which doesn't match the account's shard, or missing the shard altogether, will not work.

## [link  to api-keys-and-api-urls](https://docs.api.cliniko.com/guides/sharding\#api-keys-and-api-urls) API keys and API URLs

To make is easy for integrators to know which shard to choose for an account the shard ID is appended to the end of all API keys. eg

```
MS0xLWl4SzYYYYdtR3V2HNOTAREALKEYwvNHI2d2xHHHHjLXuytrF0ZV9sdeW0pd-au1

```

The characters after the dash tell you which shard this API key may be used against.

When a Cliniko user supplies their API key, you will need to use the shard ID when making API requests on behalf of users of that account.

For example:

- An API key ending `-uk1` must have all API requests routed to `https://api.uk1.cliniko.com`
- An API key ending `-ca1` must have all API requests routed to `https://api.ca1.cliniko.com`
- An API key ending `-au1` should have all API requests routed to `https://api.au1.cliniko.com`

The API key is passed in the Basic authorization header, just as you do now: `b64($API_KEY + ':')` and you may **include or exclude** the hyphenated shard ID. That is, if you make an API request using either `MS0xLWl4SzYY-uk1` or `MS0xLWl4SzYY`, the request will succeed. You just need to ensure you're sending the request to the correct shard (in this case, `uk1`).

### [link  to older-api-keys](https://docs.api.cliniko.com/guides/sharding\#older-api-keys) Older API keys

Any API keys generated prior to the introduction of sharding may not include the shard suffix but they will all belong to the `au1` shard. The key can effectively be written as:

```
{THE_API_KEY_VALUE}-au1

```

> For existing API keys, you should be using the default shard `au1`. Eventually the current Cliniko API URL will start redirecting with a `301`, only responding to requests on the sharded routes.

### [link  to code-examples](https://docs.api.cliniko.com/guides/sharding\#code-examples) Code examples

While these examples are not designed to work, they should give you a good idea of how your API key usage should change.

#### [link  to saving-an-api-key](https://docs.api.cliniko.com/guides/sharding\#saving-an-api-key) Saving an API key

```
function saveApiKey(apiKeyInput, accountId) {
  var apiKeyParts = apiKeyInput.split('-');
  var apiKey = null;
  var shardId = null;

  if (apiKeyParts.length === 1) {
    // If no shard ID supplied, default it in.
    apiKey = apiKeyParts[0];
    shardId = 'au1';
  } else if (apiKeyParts.length === 2 && /^\w{2}\d{1,2}$/.test(apiKeyParts[1])) {
    // Otherwise, use the shard ID supplied to you, ensuring it matches known attributes
    // e.g. two alpha chars followed by 1-2 digits
    apiKey = apiKeyParts[0];
    // Maybe also validate it against the list of current shard regions?
    shardId = apiKeyParts[1];
  } else {
    throw new Error('Invalid API key');
  }

  var clinikoIntegration = new ClinikoIntegration({
    accountId: accountId,
    apiKey: apiKey,
    shardId: shardId
  });
  clinikoIntegration.save();
}

```

#### [link  to using-an-api-key](https://docs.api.cliniko.com/guides/sharding\#using-an-api-key) Using an API key

```
function requestClinikoPatient(patientId, accountId) {
  var clinikoIntegration = ClinikoIntegration.findOne({ accountId: accountId });

  // If you don't have a shard ID saved, use the default au1.
  var shardId = clinikoIntegration.shardId || 'au1';
  var requestOpts = {
    url: 'https://api.' + shardId + '.cliniko.com/v1/patients/' + patientId,
    method: 'GET',
    headers: {
      authorization: 'Basic ' + base64(clinikoIntegration.apiKey + ':'),
      'user-agent': 'Your name (integrations@example.com)',
      accept: 'application/json',
      'content-type': 'application/json'
    }
  };
  var patient = request(requestOpts);
  // Do helpful things...
}

```

Previous page [Base URL and Shards](https://docs.api.cliniko.com/guides/urls)

Next page [Telehealth links](https://docs.api.cliniko.com/guides/telehealth_links)