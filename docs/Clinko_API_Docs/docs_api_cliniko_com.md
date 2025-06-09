Introduction

Last updated 3 months ago

# [link  to introduction](https://docs.api.cliniko.com/\#introduction) Introduction

This is the official API for Cliniko. Cliniko is a practice management system for healthcare practitioners.

The Cliniko API is based on REST principles. This means you can use any HTTP client and any programming language to interact with the API.

JSON will be returned in all responses from the API.

## [link  to security](https://docs.api.cliniko.com/\#security) Security

The Cliniko API is served over HTTPS to ensure data security and privacy. HTTP is not supported.

Ensure that the HTTP client is up-to-date and has the latest TLS (minimum of 1.2), cipher suites and SNI available. It's recommended that the client uses the cipher offered by the Cliniko API. It's _not recommended_ to hard-code TLS versions or ciphers.

Warning

An API Key from Cliniko will allow access to sensitive information.Handle the key securely like you would a password.

## [link  to authentication](https://docs.api.cliniko.com/\#authentication) Authentication

The Cliniko API uses HTTP Basic authentication. This is secure, as all requests are via SSL.

Each Cliniko user will have their own API key(s) - these are used for authentication. The API key will have the same permissions as the user it belongs to.

You should provide the Cliniko API key (either with or without the shard suffix) as the basic auth username. There is no need to provide a password. This should be sent in the `Authorization` header. The pseudocode for how the `Authorization` header should be built is:

```
"Basic " + base64_encode(api_key + ":")

```

For example, if your API key is `MxJrZXkiOiI1Njd1amJmZTQ1NyJ9-au2`, then you would generate your Authorization header like so, using the API key as the username:

```
"Basic " + base64_encode("MxJrZXkiOiI1Njd1amJmZTQ1NyJ9-au2" + ":")

```

resulting in your Authorization header value:

```
Basic TXhKclpYa2lPaUkxTmpkMWFtSm1aVFExTnlKOS1hdTI6

```

To obtain an API key for testing, sign up for a free trial and go to the "My Info" link in the bottom left corner of the navigation within Cliniko. Click the "Manage API keys" button, you can create an API key from that page. If you need your trial extended just let us know.

Warning

An API Key from Cliniko will allow access to sensitive information.Handle the key securely like you would a password.

## [link  to identifying-your-application](https://docs.api.cliniko.com/\#identifying-your-application) Identifying your application

To identify your application, you need to send the `User-Agent` header. In the event of an issue, this allows us to easily track down your requests and contact you. This should be in the form:

```
APP_VENDOR_NAME (APP_VENDOR_EMAIL)

```

**`APP_VENDOR_NAME`** is the name of your application **`APP_VENDOR_EMAIL`** is a contact email address for you or your company

As an example, a valid `User-Agent` value would be something like:

```
Really helpful app (devs@helpfulapp.com)

```

Attention

If your requests do not include a User-Agent that contains a name and valid contact email, future requests may be automatically blocked.

## [link  to errors](https://docs.api.cliniko.com/\#errors) Errors

Conventional HTTP response codes are used to indicate API errors.

General code rules apply:

- 2xx range indicate success
- 4xx range indicate an error resulting from the provided information (eg. missing a required parameter)
- 5xx range indicate an error with our Cliniko servers

## [link  to making-a-request](https://docs.api.cliniko.com/\#making-a-request) Making a request

To make a request append the endpoint path to the base URL.

For example to get all the patients on a specific account in the `au1` shard, you'd append the patients index path to the base and make a request.

In curl:

```
curl https://api.au1.cliniko.com/v1/patients \
  -u API_KEY: \
  -H 'Accept: application/json' \
  -H 'User-Agent: APP_VENDOR_NAME (APP_VENDOR_EMAIL)'

```

_Note: curl uses the -u flag to pass basic auth credentials (adding a colon after the API key will prevent it from asking for a password)._

**API\_KEY** is the API key provided by the Cliniko user.

Make sure to send the `Accept` header with `application/json` and the user agent for your app.

That's all!

## [link  to rate-limits](https://docs.api.cliniko.com/\#rate-limits) Rate limits

API requests are rate limited to 200 per minute per user. We recommend you design your app to stagger requests to avoid hitting the rate limit.

Requests exceeding the rate limit will receive a response with a 429 status and an `X-RateLimit-Reset` header containing the time at which the limit will reset. The time is formatted as a UNIX timestamp of elapsed seconds since the start of the UNIX epoch in the UTC timezone.

Requests that exceed our fair use allocation may be blocked. If you require a higher rate limit, please contact us.

## [link  to data-responses](https://docs.api.cliniko.com/\#data-responses) Data Responses

We only support JSON for serialization of data.

## [link  to dates-and-times](https://docs.api.cliniko.com/\#dates-and-times) Dates and Times

All dates and times are expected to be in UTC.

## [link  to pagination](https://docs.api.cliniko.com/\#pagination) Pagination

Requests that return multiple items will be paginated to 50 items by default. You can specify further pages with the `page` parameter. You can also set a custom page size up to 100 with the `per_page` parameter.

All paginated requests will return the total number of entries that exist as `total_entries` in the response.

The pagination info is included in the `links` object. It is recommended to follow these links instead of constructing your own URLs.

```
"appointments": {
  ...
},
total_entries: 400,
"links": {
  "next": "https://api.au1.cliniko.com/v1/appointments?page=4&per_page=100",
  "self": "https://api.au1.cliniko.com/v1/appointments?page=3&per_page=100",
  "previous": "https://api.au1.cliniko.com/v1/appointments?page=2&per_page=100"
}

```

The possible pagination links are:

`next` Shows the URL of the immediate next page of results.

`self` Shows the URL of the current page of results.

`previous` Shows the URL of the immediate previous page of results.

The pagination links will only be included if they are relevant, eg. there will be no `next` link if you are on the last page.

## [link  to filtering-results](https://docs.api.cliniko.com/\#filtering-results) Filtering Results

Some resources allow the results to be filtered. This will be documented with the resource if it is available.

### [link  to date-filter-operators](https://docs.api.cliniko.com/\#date-filter-operators) Date Filter Operators

| Operator | Description |
| :-: | --- |
| `=` | Equal to |
| `>=` | Greater than or equal to |
| `>` | Greater than |
| `<=` | Less than or equal to |
| `<` | Less than |
| `?` | Is not null |
| `!?` | Is null |

Dates must be in `YYYY-MM-DD format`. The date filter accepts wildcards in this format using `*`. Ex: `****-05-**` will return all patients born in May.

### [link  to datetime-filter-operators](https://docs.api.cliniko.com/\#datetime-filter-operators) DateTime Filter Operators

| Operator | Description |
| :-: | --- |
| `>=` | Greater than or equal to |
| `>` | Greater than |
| `<=` | Less than or equal to |
| `<` | Less than |
| `?` | Is not null |
| `!?` | Is null |
| `*` | Any value |

DateTimes must be in UTC if present – e.g. `2014-08-30T18:00:00Z`.

The `*` operator can be used to find cancelled or archived records on an endpoint that would usually exclude them - see [example](https://docs.api.cliniko.com/#example-request-all-records-including-archived) .

### [link  to numeric-filter-operators](https://docs.api.cliniko.com/\#numeric-filter-operators) Numeric Filter Operators

| Operator | Description |
| :-: | --- |
| `=` | Equal to |
| `!=` | Not equal to |
| `>=` | Greater than or equal to |
| `>` | Greater than |
| `<=` | Less than or equal to |
| `<` | Less than |
| `?` | Is not null |
| `!?` | Is null |

The `=` operator also accepts a list of numbers in the format: `[FIELDNAME]:=[VALUE],[VALUE],[VALUE],[VALUE]`. For example, `practitioner_id:=1,2,3` will return all records with practitioner\_id of 1, 2 or 3.

### [link  to string-filter-operators](https://docs.api.cliniko.com/\#string-filter-operators) String Filter Operators

| Operator | Description |
| :-: | --- |
| `=` | Equal to |
| `!=` | Not equal to |
| `~` | Contains |
| `~~` | Wildcard search ( `%`) |
| `?` | Is not null |
| `!?` | Is null |

### [link  to boolean-filter-operators](https://docs.api.cliniko.com/\#boolean-filter-operators) Boolean Filter Operators

| Operator | Description |
| :-: | --- |
| `=` | Equal to |
| `!=` | Not equal to |

### [link  to array-filter-operators](https://docs.api.cliniko.com/\#array-filter-operators) Array Filter Operators

| Operator | Description |
| :-: | --- |
| `~` | Contains |

### [link  to filtering-format](https://docs.api.cliniko.com/\#filtering-format) Filtering Format

The format for filtering a field is `[FIELDNAME]:[OPERATOR][VALUE]`

### [link  to sending-filter-parameters](https://docs.api.cliniko.com/\#sending-filter-parameters) Sending Filter Parameters

To filter a resource, send the field filter with the `q[]` parameter:

`https://api.au1.cliniko.com/v1/individual_appointments?q[]=starts_at:>2014-03-04T20:37:17Z`

To apply multiple filters, send each field filter with a separate `q[]` parameter:

`https://api.au1.cliniko.com/v1/individual_appointments?q[]=starts_at:>2014-03-04T20:37:17Z&q[]=starts_at:<2014-04-04T20:37:17Z`

#### [link  to example-request-greater-than](https://docs.api.cliniko.com/\#example-request-greater-than) Example Request (Greater than)

```
curl https://api.au1.cliniko.com/v1/individual_appointments?q[]=starts_at:>2014-03-04T20:37:17Z \
  -u API_KEY: \
  -H 'Accept: application/json' \
  -H 'User-Agent: APP_VENDOR_NAME (APP_VENDOR_EMAIL)'

```

#### [link  to example-request-contains](https://docs.api.cliniko.com/\#example-request-contains) Example Request (Contains)

```
curl https://api.au1.cliniko.com/v1/patients?q[]=last_name:~son \
  -u API_KEY: \
  -H 'Accept: application/json' \
  -H 'User-Agent: APP_VENDOR_NAME (APP_VENDOR_EMAIL)'

```

#### [link  to example-request-wildcard-search](https://docs.api.cliniko.com/\#example-request-wildcard-search) Example Request (Wildcard search)

```
curl https://api.au1.cliniko.com/v1/patients?q[]=last_name:~~ja%on% \
  -u API_KEY: \
  -H 'Accept: application/json' \
  -H 'User-Agent: APP_VENDOR_NAME (APP_VENDOR_EMAIL)'

```

#### [link  to example-request-all-records-including-archived](https://docs.api.cliniko.com/\#example-request-all-records-including-archived) Example Request (All records including archived)

```
curl https://api.au1.cliniko.com/v1/individual_appointments?q[]=archived_at:* \
  -u API_KEY: \
  -H 'Accept: application/json' \
  -H 'User-Agent: APP_VENDOR_NAME (APP_VENDOR_EMAIL)'

```

#### [link  to example-request-multiple-filters](https://docs.api.cliniko.com/\#example-request-multiple-filters) Example Request (Multiple filters)

```
curl https://api.au1.cliniko.com/v1/patients?q%5B%5D=first_name:~bri&q%5B%5D=last_name:~son \
  -u API_KEY: \
  -H 'Accept: application/json' \
  -H 'User-Agent: APP_VENDOR_NAME (APP_VENDOR_EMAIL)'

```

In this example, `q[]` is encoded as `q%5B%5D` so this command works properly in a terminal.

### [link  to filtering-tips](https://docs.api.cliniko.com/\#filtering-tips) Filtering Tips

- `%` is the wildcard symbol for the **wildcard search** operator. You may need to escape it ( `%25`).
- You can use multiple `%` s in a **wildcard search**.
- The **contains** operator is the same as doing `%value%` with the **wildcard search**.
- You can get records that have been updated since a certain time by sending a filter for `updated_at`. Ex: `q[]=updated_at:>2014-08-30T18:00:00Z`

## [link  to ordering](https://docs.api.cliniko.com/\#ordering) Ordering

By default, API results are ordered in ascending direction by their `created_at` timestamps.

You can specify a custom column to order by sending the `sort` parameter as the column name (eg. `sort=appointment_start`). You can also send multiple columns to sort by (eg. `sort=appointment_start,created_at`).

You can also specify the order direction by sending the `order` parameter set to `desc` or `asc` (eg. `order=desc`). If you need to order a column in the other direction, you can specify the order in the `sort` parameter (eg. `sort=appointment_start,created_at:desc`).

Availability times are not able to be custom ordered, they are always returned chronologically.

## [link  to stay-up-to-date-and-get-involved](https://docs.api.cliniko.com/\#stay-up-to-date-and-get-involved) Stay up to date and get involved

Join [Cliniko API Developers Group](https://groups.google.com/a/redguava.com.au/d/forum/cliniko-api) to stay updated with any changes and exchange information with Cliniko API Developers and others using the API.

If you are relying on the Cliniko API please subscribe to our [system status updates](https://status.cliniko.com/).

For feature requests or bugs please use GitHub issues. You can also fork this project and send a pull request with any improvements.

Need to talk to us privately? Send an email through to support@cliniko.com and we'll make sure it gets to the developers.

Warning

Do not send any real Cliniko API key to the Google Group, or via email.Doing so may result in your application being blocked for security concerns.

Next page [Base URL and Shards](https://docs.api.cliniko.com/guides/urls)