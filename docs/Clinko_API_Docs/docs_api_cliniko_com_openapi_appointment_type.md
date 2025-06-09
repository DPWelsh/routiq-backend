Cliniko API

# Cliniko API(v1)

This is the official API for Cliniko. Cliniko is a practice management system for healthcare practitioners.

The Cliniko API is based on REST principles. This means you can use any HTTP client and any programming language to interact with the API.

JSON will be returned in all responses from the API.

[Clinko API Developers Group](https://groups.google.com/a/redguava.com.au/d/forum/cliniko-api)

Download OpenAPI description

[openapi.json](https://docs.api.cliniko.com/_spec/openapi.json?download)

[openapi.yaml](https://docs.api.cliniko.com/_spec/openapi.yaml?download)

Languages

curlJavaScriptPythonRuby

Servers

Production

https://api.au1.cliniko.com/v1/

## [link to Appointment Type](https://docs.api.cliniko.com/openapi/appointment-type) Appointment Type

Operations

get

/appointment\_types

post

/appointment\_types

get

/appointment\_types/{id}

patch

/appointment\_types/{id}

post

/appointment\_types/{id}/archive

get

/practitioners/{practitioner\_id}/appointment\_types

delete

/appointment\_types/{id}Deprecated

## [link to AppointmentType](https://docs.api.cliniko.com/openapi/appointment-type/appointmenttype) AppointmentType

[link to #path=add_deposit_to_account_credit](https://docs.api.cliniko.com/openapi/appointment-type#path=add_deposit_to_account_credit) add\_deposit\_to\_account\_credit _boolean or null_

[link to #path=appointment_confirmation_template_ids](https://docs.api.cliniko.com/openapi/appointment-type#path=appointment_confirmation_template_ids) appointment\_confirmation\_template\_ids _Array of strings or null_ _(int64)_

Example:\["1"\]

[link to #path=appointment_reminder_template_ids](https://docs.api.cliniko.com/openapi/appointment-type#path=appointment_reminder_template_ids) appointment\_reminder\_template\_ids _Array of strings or null_ _(int64)_

Example:\["1"\]

[link to #path=appointment_type_billable_items](https://docs.api.cliniko.com/openapi/appointment-type#path=appointment_type_billable_items) appointment\_type\_billable\_items _object_

+Show property

[link to #path=appointment_type_products](https://docs.api.cliniko.com/openapi/appointment-type#path=appointment_type_products) appointment\_type\_products _object_

+Show property

[link to #path=archived_at](https://docs.api.cliniko.com/openapi/appointment-type#path=archived_at) archived\_at _string or null_ _(date-time)_

[link to #path=category](https://docs.api.cliniko.com/openapi/appointment-type#path=category) category _string or null_

[link to #path=color](https://docs.api.cliniko.com/openapi/appointment-type#path=color) color _string_ ^#(\[A-Fa-f0-9\]{6}\|\[A-Fa-f0-9\]{3})$

[link to #path=created_at](https://docs.api.cliniko.com/openapi/appointment-type#path=created_at) created\_at _string_ _(date-time)_

[link to #path=deposit_price](https://docs.api.cliniko.com/openapi/appointment-type#path=deposit_price) deposit\_price _string or null_ _(decimal)_ _\[ 0 .. 4000000000 )_\
\
[link to #path=description](https://docs.api.cliniko.com/openapi/appointment-type#path=description) description _string or null_\
\
[link to #path=duration_in_minutes](https://docs.api.cliniko.com/openapi/appointment-type#path=duration_in_minutes) duration\_in\_minutes _integer_ _( 0 .. 1440 )_\
\
[link to #path=id](https://docs.api.cliniko.com/openapi/appointment-type#path=id) id _string_ _(int64)_\
\
[link to #path=links](https://docs.api.cliniko.com/openapi/appointment-type#path=links) links _object_\
\
+Show property\
\
[link to #path=max_attendees](https://docs.api.cliniko.com/openapi/appointment-type#path=max_attendees) max\_attendees _integer_ _( 0 .. 100 )_\
\
[link to #path=name](https://docs.api.cliniko.com/openapi/appointment-type#path=name) name _string_ _<= 255 characters_\
\
[link to #path=online_bookings_lead_time_hours](https://docs.api.cliniko.com/openapi/appointment-type#path=online_bookings_lead_time_hours) online\_bookings\_lead\_time\_hours _integer or null_\
\
Enum01241218244872168+3 more\
\
[link to #path=online_payments_enabled](https://docs.api.cliniko.com/openapi/appointment-type#path=online_payments_enabled) online\_payments\_enabled _boolean or null_\
\
[link to #path=online_payments_mode](https://docs.api.cliniko.com/openapi/appointment-type#path=online_payments_mode) online\_payments\_mode _string or null_\
\
Enum"deposit\_required""optional""required"\
\
[link to #path=practitioners](https://docs.api.cliniko.com/openapi/appointment-type#path=practitioners) practitioners _object_\
\
+Show property\
\
[link to #path=show_in_online_bookings](https://docs.api.cliniko.com/openapi/appointment-type#path=show_in_online_bookings) show\_in\_online\_bookings _boolean or null_\
\
[link to #path=telehealth_enabled](https://docs.api.cliniko.com/openapi/appointment-type#path=telehealth_enabled) telehealth\_enabled _boolean or null_\
\
[link to #path=treatment_note_template](https://docs.api.cliniko.com/openapi/appointment-type#path=treatment_note_template) treatment\_note\_template _object_\
\
+Show property\
\
[link to #path=updated_at](https://docs.api.cliniko.com/openapi/appointment-type#path=updated_at) updated\_at _string_ _(date-time)_\
\
[link to #path=billable_item](https://docs.api.cliniko.com/openapi/appointment-type#path=billable_item) billable\_item _object_ Deprecated\
\
+Show property\
\
[link to #path=product](https://docs.api.cliniko.com/openapi/appointment-type#path=product) product _object_ Deprecated\
\
+Show property\
\
```\
\
{\
  "add_deposit_to_account_credit": true,\
  "appointment_confirmation_template_ids": [\
    "1"\
  ],\
  "appointment_reminder_template_ids": [\
    "1"\
  ],\
  "appointment_type_billable_items": {\
    "links": {\
      "self": "https://api.au1.cliniko.com/v1/appointment_type_billable_items?q%5B%5D=appointment_type_id%3A%3D1"\
    }\
  },\
  "appointment_type_products": {\
    "links": {\
      "self": "https://api.au1.cliniko.com/v1/appointment_type_products?q%5B%5D=appointment_type_id%3A%3D1"\
    }\
  },\
  "archived_at": "2019-08-24T14:15:22Z",\
  "billable_item": {\
    "links": {\
      "self": "https://api.au1.cliniko.com/v1/billable_items/1"\
    }\
  },\
  "category": "string",\
  "color": "string",\
  "created_at": "2019-08-24T14:15:22Z",\
  "deposit_price": "string",\
  "description": "string",\
  "duration_in_minutes": 0,\
  "id": "string",\
  "links": {\
    "self": "https://api.au1.cliniko.com/v1/appointment_types/1"\
  },\
  "max_attendees": 0,\
  "name": "string",\
  "online_bookings_lead_time_hours": 0,\
  "online_payments_enabled": true,\
  "online_payments_mode": "deposit_required",\
  "practitioners": {\
    "links": {\
      "self": "https://api.au1.cliniko.com/v1/practitioners?q%5B%5D=appointment_type_id%3A%3D1"\
    }\
  },\
  "product": {\
    "links": {\
      "self": "https://api.au1.cliniko.com/v1/products/1"\
    }\
  },\
  "show_in_online_bookings": true,\
  "telehealth_enabled": true,\
  "treatment_note_template": {\
    "links": {\
      "self": "https://api.au1.cliniko.com/v1/treatment_note_templates/1"\
    }\
  },\
  "updated_at": "2019-08-24T14:15:22Z"\
}\
```\
\
## [link to List appointment types](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypes-get) List appointment types\
\
#### [link to /appointment-type/listappointmenttypes-get\#appointment-type/listappointmenttypes-get/request](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypes-get\#appointment-type/listappointmenttypes-get/request) Request\
\
Security:\
\
basicAuth\
\
\
\
[link to /appointment-type/listappointmenttypes-get#appointment-type/listappointmenttypes-get/request/query](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypes-get#appointment-type/listappointmenttypes-get/request/query) Query\
\
[link to /appointment-type/listappointmenttypes-get#appointment-type/listappointmenttypes-get/t=request&in=query&path=page](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypes-get#appointment-type/listappointmenttypes-get/t=request&in=query&path=page) page _integer_\
\
[link to /appointment-type/listappointmenttypes-get#appointment-type/listappointmenttypes-get/t=request&in=query&path=per_page](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypes-get#appointment-type/listappointmenttypes-get/t=request&in=query&path=per_page) per\_page _integer_ _\[ 1 .. 100 \]_\
\
[link to /appointment-type/listappointmenttypes-get#appointment-type/listappointmenttypes-get/t=request&in=query&path=sort](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypes-get#appointment-type/listappointmenttypes-get/t=request&in=query&path=sort) sort _Array of strings_\
\
Comma separated search fields. See: [Ordering](https://docs.api.cliniko.com/#ordering)\
\
Example:sort=created\_at:desc\
\
[link to /appointment-type/listappointmenttypes-get#appointment-type/listappointmenttypes-get/t=request&in=query&path=q[]](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypes-get#appointment-type/listappointmenttypes-get/t=request&in=query&path=q[]) q\[\] _Array of strings_\
\
Filter result by one or more fields.\
\
See [Filtering Results](https://docs.api.cliniko.com/#filtering-results)\
\
Available filters:\
\
| Value | Format |\
| --- | --- |\
| appointment\_confirmation\_template\_ids | [array](https://docs.api.cliniko.com/#array-filter-operators) |\
| appointment\_reminder\_template\_ids | [array](https://docs.api.cliniko.com/#array-filter-operators) |\
| archived\_at | [date-time](https://docs.api.cliniko.com/#datetime-filter-operators) |\
| category | [string](https://docs.api.cliniko.com/#string-filter-operators) |\
| created\_at | [date-time](https://docs.api.cliniko.com/#datetime-filter-operators) |\
| id | [int64](https://docs.api.cliniko.com/#numeric-filter-operators) |\
| online\_payments\_mode | [string](https://docs.api.cliniko.com/#string-filter-operators) |\
| show\_in\_online\_bookings | [boolean](https://docs.api.cliniko.com/#boolean-filter-operators) |\
| updated\_at | [date-time](https://docs.api.cliniko.com/#datetime-filter-operators) |\
\
[link to /appointment-type/listappointmenttypes-get#appointment-type/listappointmenttypes-get/t=request&in=query&path=order](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypes-get#appointment-type/listappointmenttypes-get/t=request&in=query&path=order) order _string_ Deprecated\
\
Enum"asc""desc"\
\
get\
\
/appointment\_types\
\
- Productionhttps://api.au1.cliniko.com/v1/appointment\_types\
\
\
curl\
\
- curl\
- JavaScript\
- Python\
- Ruby\
\
```\
curl -i -X GET \\
  -u <username>:<password> \\
  'https://api.au1.cliniko.com/v1/appointment_types?order=asc&page=0&per_page=1&q%5B%5D=string&sort=created_at%3Adesc'\
```\
\
#### [link to /appointment-type/listappointmenttypes-get\#appointment-type/listappointmenttypes-get/response&c=200](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypes-get\#appointment-type/listappointmenttypes-get/response&c=200) Responses\
\
1. 200\
\
Expand all\
\
successful operation\
\
[link to /appointment-type/listappointmenttypes-get#appointment-type/listappointmenttypes-get/response&c=200/body](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypes-get#appointment-type/listappointmenttypes-get/response&c=200/body) Bodyapplication/json\
\
[link to /appointment-type/listappointmenttypes-get#appointment-type/listappointmenttypes-get/t=response&c=200&path=appointment_types](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypes-get#appointment-type/listappointmenttypes-get/t=response&c=200&path=appointment_types) appointment\_types _Array of objects_ _(AppointmentType)_\
\
+Show 26 array properties\
\
[link to /appointment-type/listappointmenttypes-get#appointment-type/listappointmenttypes-get/t=response&c=200&path=total_entries](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypes-get#appointment-type/listappointmenttypes-get/t=response&c=200&path=total_entries) total\_entries _integer_\
\
Example:1\
\
[link to /appointment-type/listappointmenttypes-get#appointment-type/listappointmenttypes-get/t=response&c=200&path=links](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypes-get#appointment-type/listappointmenttypes-get/t=response&c=200&path=links) links _object_\
\
+Show 3 properties\
\
Response\
\
1. 200\
\
application/json\
\
```\
\
{\
  "appointment_types": [\
    {\
      "add_deposit_to_account_credit": true,\
      "appointment_confirmation_template_ids": [\
        "1"\
      ],\
      "appointment_reminder_template_ids": [\
        "1"\
      ],\
      "appointment_type_billable_items": {\
        "links": { … }\
      },\
      "appointment_type_products": {\
        "links": { … }\
      },\
      "archived_at": "2019-08-24T14:15:22Z",\
      "billable_item": {\
        "links": { … }\
      },\
      "category": "string",\
      "color": "string",\
      "created_at": "2019-08-24T14:15:22Z",\
      "deposit_price": "string",\
      "description": "string",\
      "duration_in_minutes": 0,\
      "id": "string",\
      "links": {\
        "self": "https://api.au1.cliniko.com/v1/appointment_types/1"\
      },\
      "max_attendees": 0,\
      "name": "string",\
      "online_bookings_lead_time_hours": 0,\
      "online_payments_enabled": true,\
      "online_payments_mode": "deposit_required",\
      "practitioners": {\
        "links": { … }\
      },\
      "product": {\
        "links": { … }\
      },\
      "show_in_online_bookings": true,\
      "telehealth_enabled": true,\
      "treatment_note_template": {\
        "links": { … }\
      },\
      "updated_at": "2019-08-24T14:15:22Z"\
    }\
  ],\
  "total_entries": 1,\
  "links": {\
    "self": "https://api.au1.cliniko.com/v1/appointment_types?page=2",\
    "previous": "https://api.au1.cliniko.com/v1/appointment_types?page=1",\
    "next": "https://api.au1.cliniko.com/v1/appointment_types?page=3"\
  }\
}\
```\
\
## [link to Create appointment type](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post) Create appointment type\
\
#### [link to /appointment-type/createappointmenttype-post\#appointment-type/createappointmenttype-post/request](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post\#appointment-type/createappointmenttype-post/request) Request\
\
Security:\
\
basicAuth\
\
\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/request/body](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/request/body) Bodyapplication/jsonrequired\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=add_deposit_to_account_credit](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=add_deposit_to_account_credit) add\_deposit\_to\_account\_credit _boolean or null_\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=category](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=category) category _string or null_\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=color](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=color) color _string_ ^#(\[A-Fa-f0-9\]{6}\|\[A-Fa-f0-9\]{3})$\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=deposit_price](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=deposit_price) deposit\_price _string or null_ _(decimal)_ _\[ 0 .. 4000000000 )_\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=description](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=description) description _string or null_\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=duration_in_minutes](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=duration_in_minutes) duration\_in\_minutes _integer_ _( 0 .. 1440 )_\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=online_bookings_lead_time_hours](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=online_bookings_lead_time_hours) online\_bookings\_lead\_time\_hours _integer or null_\
\
Enum01241218244872168+3 more\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=online_payments_mode](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=online_payments_mode) online\_payments\_mode _string or null_\
\
Enum"deposit\_required""optional""required"\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=max_attendees](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=max_attendees) max\_attendees _integer_ _( 0 .. 100 )_\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=name](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=name) name _string_ _<= 255 characters_\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=show_in_online_bookings](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=show_in_online_bookings) show\_in\_online\_bookings _boolean or null_\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=telehealth_enabled](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=telehealth_enabled) telehealth\_enabled _boolean or null_\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=treatment_note_template_id](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=treatment_note_template_id) treatment\_note\_template\_id _string_ _(int64)_\
\
treatment note template id\
\
Example:"1"\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=appointment_confirmation_template_ids](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=appointment_confirmation_template_ids) appointment\_confirmation\_template\_ids _Array of strings or null_ _(int64)_\
\
Example:\["1"\]\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=appointment_reminder_template_ids](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=appointment_reminder_template_ids) appointment\_reminder\_template\_ids _Array of strings or null_ _(int64)_\
\
Example:\["1"\]\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=business_ids](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=business_ids) business\_ids _Array of strings_ _(int64)_\
\
Example:\["1"\]\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=practitioner_ids](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=practitioner_ids) practitioner\_ids _Array of strings_ _(int64)_\
\
Practitioner ids\
\
Example:\["1"\]\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=billable_item_id](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=billable_item_id) billable\_item\_id _string_ _(int64)_ Deprecated\
\
billable item id\
\
Example:"1"\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=product_id](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=request&path=product_id) product\_id _string_ _(int64)_ Deprecated\
\
product id\
\
Example:"1"\
\
post\
\
/appointment\_types\
\
- Productionhttps://api.au1.cliniko.com/v1/appointment\_types\
\
\
curl\
\
- curl\
- JavaScript\
- Python\
- Ruby\
\
```\
curl -i -X POST \\
  -u <username>:<password> \\
  https://api.au1.cliniko.com/v1/appointment_types \\
  -H 'Content-Type: application/json' \\
  -d '{\
    "add_deposit_to_account_credit": true,\
    "billable_item_id": "1",\
    "category": "string",\
    "color": "string",\
    "deposit_price": "string",\
    "description": "string",\
    "duration_in_minutes": 0,\
    "online_bookings_lead_time_hours": 0,\
    "online_payments_mode": "deposit_required",\
    "max_attendees": 0,\
    "name": "string",\
    "product_id": "1",\
    "show_in_online_bookings": true,\
    "telehealth_enabled": true,\
    "treatment_note_template_id": "1",\
    "appointment_confirmation_template_ids": [\
      "1"\
    ],\
    "appointment_reminder_template_ids": [\
      "1"\
    ],\
    "business_ids": [\
      "1"\
    ],\
    "practitioner_ids": [\
      "1"\
    ]\
  }'\
```\
\
#### [link to /appointment-type/createappointmenttype-post\#appointment-type/createappointmenttype-post/response&c=201](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post\#appointment-type/createappointmenttype-post/response&c=201) Responses\
\
1. 201\
2. 422\
\
Expand all\
\
Resource was created\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/response&c=201/body](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/response&c=201/body) Bodyapplication/json\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=add_deposit_to_account_credit](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=add_deposit_to_account_credit) add\_deposit\_to\_account\_credit _boolean or null_\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=appointment_confirmation_template_ids](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=appointment_confirmation_template_ids) appointment\_confirmation\_template\_ids _Array of strings or null_ _(int64)_\
\
Example:\["1"\]\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=appointment_reminder_template_ids](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=appointment_reminder_template_ids) appointment\_reminder\_template\_ids _Array of strings or null_ _(int64)_\
\
Example:\["1"\]\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=appointment_type_billable_items](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=appointment_type_billable_items) appointment\_type\_billable\_items _object_\
\
+Show property\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=appointment_type_products](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=appointment_type_products) appointment\_type\_products _object_\
\
+Show property\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=archived_at](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=archived_at) archived\_at _string or null_ _(date-time)_\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=category](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=category) category _string or null_\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=color](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=color) color _string_ ^#(\[A-Fa-f0-9\]{6}\|\[A-Fa-f0-9\]{3})$\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=created_at](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=created_at) created\_at _string_ _(date-time)_\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=deposit_price](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=deposit_price) deposit\_price _string or null_ _(decimal)_ _\[ 0 .. 4000000000 )_\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=description](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=description) description _string or null_\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=duration_in_minutes](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=duration_in_minutes) duration\_in\_minutes _integer_ _( 0 .. 1440 )_\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=id](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=id) id _string_ _(int64)_\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=links](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=links) links _object_\
\
+Show property\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=max_attendees](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=max_attendees) max\_attendees _integer_ _( 0 .. 100 )_\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=name](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=name) name _string_ _<= 255 characters_\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=online_bookings_lead_time_hours](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=online_bookings_lead_time_hours) online\_bookings\_lead\_time\_hours _integer or null_\
\
Enum01241218244872168+3 more\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=online_payments_enabled](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=online_payments_enabled) online\_payments\_enabled _boolean or null_\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=online_payments_mode](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=online_payments_mode) online\_payments\_mode _string or null_\
\
Enum"deposit\_required""optional""required"\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=practitioners](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=practitioners) practitioners _object_\
\
+Show property\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=show_in_online_bookings](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=show_in_online_bookings) show\_in\_online\_bookings _boolean or null_\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=telehealth_enabled](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=telehealth_enabled) telehealth\_enabled _boolean or null_\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=treatment_note_template](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=treatment_note_template) treatment\_note\_template _object_\
\
+Show property\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=updated_at](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=updated_at) updated\_at _string_ _(date-time)_\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=billable_item](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=billable_item) billable\_item _object_ Deprecated\
\
+Show property\
\
[link to /appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=product](https://docs.api.cliniko.com/openapi/appointment-type/createappointmenttype-post#appointment-type/createappointmenttype-post/t=response&c=201&path=product) product _object_ Deprecated\
\
+Show property\
\
Response\
\
1. 201\
2. 422\
\
application/json\
\
```\
\
{\
  "add_deposit_to_account_credit": true,\
  "appointment_confirmation_template_ids": [\
    "1"\
  ],\
  "appointment_reminder_template_ids": [\
    "1"\
  ],\
  "appointment_type_billable_items": {\
    "links": {\
      "self": "https://api.au1.cliniko.com/v1/appointment_type_billable_items?q%5B%5D=appointment_type_id%3A%3D1"\
    }\
  },\
  "appointment_type_products": {\
    "links": {\
      "self": "https://api.au1.cliniko.com/v1/appointment_type_products?q%5B%5D=appointment_type_id%3A%3D1"\
    }\
  },\
  "archived_at": "2019-08-24T14:15:22Z",\
  "billable_item": {\
    "links": {\
      "self": "https://api.au1.cliniko.com/v1/billable_items/1"\
    }\
  },\
  "category": "string",\
  "color": "string",\
  "created_at": "2019-08-24T14:15:22Z",\
  "deposit_price": "string",\
  "description": "string",\
  "duration_in_minutes": 0,\
  "id": "string",\
  "links": {\
    "self": "https://api.au1.cliniko.com/v1/appointment_types/1"\
  },\
  "max_attendees": 0,\
  "name": "string",\
  "online_bookings_lead_time_hours": 0,\
  "online_payments_enabled": true,\
  "online_payments_mode": "deposit_required",\
  "practitioners": {\
    "links": {\
      "self": "https://api.au1.cliniko.com/v1/practitioners?q%5B%5D=appointment_type_id%3A%3D1"\
    }\
  },\
  "product": {\
    "links": {\
      "self": "https://api.au1.cliniko.com/v1/products/1"\
    }\
  },\
  "show_in_online_bookings": true,\
  "telehealth_enabled": true,\
  "treatment_note_template": {\
    "links": {\
      "self": "https://api.au1.cliniko.com/v1/treatment_note_templates/1"\
    }\
  },\
  "updated_at": "2019-08-24T14:15:22Z"\
}\
```\
\
## [link to Get appointment type](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get) Get appointment type\
\
#### [link to /appointment-type/getappointmenttype-get\#appointment-type/getappointmenttype-get/request](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get\#appointment-type/getappointmenttype-get/request) Request\
\
Security:\
\
basicAuth\
\
\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/request/path](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/request/path) Path\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=request&in=path&path=id](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=request&in=path&path=id) id _string_ _(int64)_ required\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/request/query](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/request/query) Query\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=request&in=query&path=q[]](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=request&in=query&path=q[]) q\[\] _Array of strings_\
\
Filter result by one or more fields.\
\
See [Filtering Results](https://docs.api.cliniko.com/#filtering-results)\
\
Available filters:\
\
| Value | Format |\
| --- | --- |\
| archived\_at | [date-time](https://docs.api.cliniko.com/#datetime-filter-operators) |\
\
get\
\
/appointment\_types/{id}\
\
- Productionhttps://api.au1.cliniko.com/v1/appointment\_types/{id}\
\
\
curl\
\
- curl\
- JavaScript\
- Python\
- Ruby\
\
```\
curl -i -X GET \\
  -u <username>:<password> \\
  'https://api.au1.cliniko.com/v1/appointment_types/{id}?q%5B%5D=string'\
```\
\
#### [link to /appointment-type/getappointmenttype-get\#appointment-type/getappointmenttype-get/response&c=200](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get\#appointment-type/getappointmenttype-get/response&c=200) Responses\
\
1. 200\
\
Expand all\
\
Successful operation\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/response&c=200/body](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/response&c=200/body) Bodyapplication/json\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=add_deposit_to_account_credit](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=add_deposit_to_account_credit) add\_deposit\_to\_account\_credit _boolean or null_\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=appointment_confirmation_template_ids](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=appointment_confirmation_template_ids) appointment\_confirmation\_template\_ids _Array of strings or null_ _(int64)_\
\
Example:\["1"\]\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=appointment_reminder_template_ids](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=appointment_reminder_template_ids) appointment\_reminder\_template\_ids _Array of strings or null_ _(int64)_\
\
Example:\["1"\]\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=appointment_type_billable_items](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=appointment_type_billable_items) appointment\_type\_billable\_items _object_\
\
+Show property\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=appointment_type_products](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=appointment_type_products) appointment\_type\_products _object_\
\
+Show property\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=archived_at](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=archived_at) archived\_at _string or null_ _(date-time)_\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=category](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=category) category _string or null_\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=color](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=color) color _string_ ^#(\[A-Fa-f0-9\]{6}\|\[A-Fa-f0-9\]{3})$\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=created_at](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=created_at) created\_at _string_ _(date-time)_\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=deposit_price](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=deposit_price) deposit\_price _string or null_ _(decimal)_ _\[ 0 .. 4000000000 )_\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=description](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=description) description _string or null_\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=duration_in_minutes](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=duration_in_minutes) duration\_in\_minutes _integer_ _( 0 .. 1440 )_\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=id](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=id) id _string_ _(int64)_\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=links](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=links) links _object_\
\
+Show property\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=max_attendees](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=max_attendees) max\_attendees _integer_ _( 0 .. 100 )_\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=name](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=name) name _string_ _<= 255 characters_\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=online_bookings_lead_time_hours](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=online_bookings_lead_time_hours) online\_bookings\_lead\_time\_hours _integer or null_\
\
Enum01241218244872168+3 more\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=online_payments_enabled](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=online_payments_enabled) online\_payments\_enabled _boolean or null_\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=online_payments_mode](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=online_payments_mode) online\_payments\_mode _string or null_\
\
Enum"deposit\_required""optional""required"\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=practitioners](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=practitioners) practitioners _object_\
\
+Show property\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=show_in_online_bookings](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=show_in_online_bookings) show\_in\_online\_bookings _boolean or null_\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=telehealth_enabled](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=telehealth_enabled) telehealth\_enabled _boolean or null_\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=treatment_note_template](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=treatment_note_template) treatment\_note\_template _object_\
\
+Show property\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=updated_at](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=updated_at) updated\_at _string_ _(date-time)_\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=billable_item](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=billable_item) billable\_item _object_ Deprecated\
\
+Show property\
\
[link to /appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=product](https://docs.api.cliniko.com/openapi/appointment-type/getappointmenttype-get#appointment-type/getappointmenttype-get/t=response&c=200&path=product) product _object_ Deprecated\
\
+Show property\
\
Response\
\
1. 200\
\
application/json\
\
```\
\
{\
  "add_deposit_to_account_credit": true,\
  "appointment_confirmation_template_ids": [\
    "1"\
  ],\
  "appointment_reminder_template_ids": [\
    "1"\
  ],\
  "appointment_type_billable_items": {\
    "links": {\
      "self": "https://api.au1.cliniko.com/v1/appointment_type_billable_items?q%5B%5D=appointment_type_id%3A%3D1"\
    }\
  },\
  "appointment_type_products": {\
    "links": {\
      "self": "https://api.au1.cliniko.com/v1/appointment_type_products?q%5B%5D=appointment_type_id%3A%3D1"\
    }\
  },\
  "archived_at": "2019-08-24T14:15:22Z",\
  "billable_item": {\
    "links": {\
      "self": "https://api.au1.cliniko.com/v1/billable_items/1"\
    }\
  },\
  "category": "string",\
  "color": "string",\
  "created_at": "2019-08-24T14:15:22Z",\
  "deposit_price": "string",\
  "description": "string",\
  "duration_in_minutes": 0,\
  "id": "string",\
  "links": {\
    "self": "https://api.au1.cliniko.com/v1/appointment_types/1"\
  },\
  "max_attendees": 0,\
  "name": "string",\
  "online_bookings_lead_time_hours": 0,\
  "online_payments_enabled": true,\
  "online_payments_mode": "deposit_required",\
  "practitioners": {\
    "links": {\
      "self": "https://api.au1.cliniko.com/v1/practitioners?q%5B%5D=appointment_type_id%3A%3D1"\
    }\
  },\
  "product": {\
    "links": {\
      "self": "https://api.au1.cliniko.com/v1/products/1"\
    }\
  },\
  "show_in_online_bookings": true,\
  "telehealth_enabled": true,\
  "treatment_note_template": {\
    "links": {\
      "self": "https://api.au1.cliniko.com/v1/treatment_note_templates/1"\
    }\
  },\
  "updated_at": "2019-08-24T14:15:22Z"\
}\
```\
\
## [link to Update appointment type](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch) Update appointment type\
\
#### [link to /appointment-type/updateappointmenttype-patch\#appointment-type/updateappointmenttype-patch/request](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch\#appointment-type/updateappointmenttype-patch/request) Request\
\
Security:\
\
basicAuth\
\
\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/request/path](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/request/path) Path\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&in=path&path=id](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&in=path&path=id) id _string_ _(int64)_ required\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/request/body](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/request/body) Bodyapplication/jsonrequired\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=add_deposit_to_account_credit](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=add_deposit_to_account_credit) add\_deposit\_to\_account\_credit _boolean or null_\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=category](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=category) category _string or null_\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=color](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=color) color _string_ ^#(\[A-Fa-f0-9\]{6}\|\[A-Fa-f0-9\]{3})$\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=deposit_price](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=deposit_price) deposit\_price _string or null_ _(decimal)_ _\[ 0 .. 4000000000 )_\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=description](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=description) description _string or null_\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=duration_in_minutes](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=duration_in_minutes) duration\_in\_minutes _integer_ _( 0 .. 1440 )_\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=online_bookings_lead_time_hours](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=online_bookings_lead_time_hours) online\_bookings\_lead\_time\_hours _integer or null_\
\
Enum01241218244872168+3 more\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=online_payments_mode](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=online_payments_mode) online\_payments\_mode _string or null_\
\
Enum"deposit\_required""optional""required"\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=max_attendees](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=max_attendees) max\_attendees _integer_ _( 0 .. 100 )_\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=name](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=name) name _string_ _<= 255 characters_\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=show_in_online_bookings](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=show_in_online_bookings) show\_in\_online\_bookings _boolean or null_\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=telehealth_enabled](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=telehealth_enabled) telehealth\_enabled _boolean or null_\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=treatment_note_template_id](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=treatment_note_template_id) treatment\_note\_template\_id _string_ _(int64)_\
\
treatment note template id\
\
Example:"1"\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=appointment_confirmation_template_ids](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=appointment_confirmation_template_ids) appointment\_confirmation\_template\_ids _Array of strings or null_ _(int64)_\
\
Example:\["1"\]\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=appointment_reminder_template_ids](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=appointment_reminder_template_ids) appointment\_reminder\_template\_ids _Array of strings or null_ _(int64)_\
\
Example:\["1"\]\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=business_ids](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=business_ids) business\_ids _Array of strings_ _(int64)_\
\
Example:\["1"\]\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=practitioner_ids](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=practitioner_ids) practitioner\_ids _Array of strings_ _(int64)_\
\
Practitioner ids\
\
Example:\["1"\]\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=billable_item_id](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=billable_item_id) billable\_item\_id _string_ _(int64)_ Deprecated\
\
billable item id\
\
Example:"1"\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=product_id](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=request&path=product_id) product\_id _string_ _(int64)_ Deprecated\
\
product id\
\
Example:"1"\
\
patch\
\
/appointment\_types/{id}\
\
- Productionhttps://api.au1.cliniko.com/v1/appointment\_types/{id}\
\
\
curl\
\
- curl\
- JavaScript\
- Python\
- Ruby\
\
```\
curl -i -X PATCH \\
  -u <username>:<password> \\
  'https://api.au1.cliniko.com/v1/appointment_types/{id}' \\
  -H 'Content-Type: application/json' \\
  -d '{\
    "add_deposit_to_account_credit": true,\
    "billable_item_id": "1",\
    "category": "string",\
    "color": "string",\
    "deposit_price": "string",\
    "description": "string",\
    "duration_in_minutes": 0,\
    "online_bookings_lead_time_hours": 0,\
    "online_payments_mode": "deposit_required",\
    "max_attendees": 0,\
    "name": "string",\
    "product_id": "1",\
    "show_in_online_bookings": true,\
    "telehealth_enabled": true,\
    "treatment_note_template_id": "1",\
    "appointment_confirmation_template_ids": [\
      "1"\
    ],\
    "appointment_reminder_template_ids": [\
      "1"\
    ],\
    "business_ids": [\
      "1"\
    ],\
    "practitioner_ids": [\
      "1"\
    ]\
  }'\
```\
\
#### [link to /appointment-type/updateappointmenttype-patch\#appointment-type/updateappointmenttype-patch/response&c=200](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch\#appointment-type/updateappointmenttype-patch/response&c=200) Responses\
\
1. 200\
2. 422\
\
Expand all\
\
Resource was updated\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/response&c=200/body](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/response&c=200/body) Bodyapplication/json\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=add_deposit_to_account_credit](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=add_deposit_to_account_credit) add\_deposit\_to\_account\_credit _boolean or null_\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=appointment_confirmation_template_ids](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=appointment_confirmation_template_ids) appointment\_confirmation\_template\_ids _Array of strings or null_ _(int64)_\
\
Example:\["1"\]\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=appointment_reminder_template_ids](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=appointment_reminder_template_ids) appointment\_reminder\_template\_ids _Array of strings or null_ _(int64)_\
\
Example:\["1"\]\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=appointment_type_billable_items](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=appointment_type_billable_items) appointment\_type\_billable\_items _object_\
\
+Show property\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=appointment_type_products](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=appointment_type_products) appointment\_type\_products _object_\
\
+Show property\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=archived_at](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=archived_at) archived\_at _string or null_ _(date-time)_\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=category](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=category) category _string or null_\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=color](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=color) color _string_ ^#(\[A-Fa-f0-9\]{6}\|\[A-Fa-f0-9\]{3})$\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=created_at](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=created_at) created\_at _string_ _(date-time)_\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=deposit_price](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=deposit_price) deposit\_price _string or null_ _(decimal)_ _\[ 0 .. 4000000000 )_\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=description](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=description) description _string or null_\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=duration_in_minutes](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=duration_in_minutes) duration\_in\_minutes _integer_ _( 0 .. 1440 )_\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=id](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=id) id _string_ _(int64)_\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=links](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=links) links _object_\
\
+Show property\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=max_attendees](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=max_attendees) max\_attendees _integer_ _( 0 .. 100 )_\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=name](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=name) name _string_ _<= 255 characters_\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=online_bookings_lead_time_hours](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=online_bookings_lead_time_hours) online\_bookings\_lead\_time\_hours _integer or null_\
\
Enum01241218244872168+3 more\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=online_payments_enabled](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=online_payments_enabled) online\_payments\_enabled _boolean or null_\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=online_payments_mode](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=online_payments_mode) online\_payments\_mode _string or null_\
\
Enum"deposit\_required""optional""required"\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=practitioners](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=practitioners) practitioners _object_\
\
+Show property\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=show_in_online_bookings](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=show_in_online_bookings) show\_in\_online\_bookings _boolean or null_\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=telehealth_enabled](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=telehealth_enabled) telehealth\_enabled _boolean or null_\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=treatment_note_template](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=treatment_note_template) treatment\_note\_template _object_\
\
+Show property\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=updated_at](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=updated_at) updated\_at _string_ _(date-time)_\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=billable_item](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=billable_item) billable\_item _object_ Deprecated\
\
+Show property\
\
[link to /appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=product](https://docs.api.cliniko.com/openapi/appointment-type/updateappointmenttype-patch#appointment-type/updateappointmenttype-patch/t=response&c=200&path=product) product _object_ Deprecated\
\
+Show property\
\
Response\
\
1. 200\
2. 422\
\
application/json\
\
```\
\
{\
  "add_deposit_to_account_credit": true,\
  "appointment_confirmation_template_ids": [\
    "1"\
  ],\
  "appointment_reminder_template_ids": [\
    "1"\
  ],\
  "appointment_type_billable_items": {\
    "links": {\
      "self": "https://api.au1.cliniko.com/v1/appointment_type_billable_items?q%5B%5D=appointment_type_id%3A%3D1"\
    }\
  },\
  "appointment_type_products": {\
    "links": {\
      "self": "https://api.au1.cliniko.com/v1/appointment_type_products?q%5B%5D=appointment_type_id%3A%3D1"\
    }\
  },\
  "archived_at": "2019-08-24T14:15:22Z",\
  "billable_item": {\
    "links": {\
      "self": "https://api.au1.cliniko.com/v1/billable_items/1"\
    }\
  },\
  "category": "string",\
  "color": "string",\
  "created_at": "2019-08-24T14:15:22Z",\
  "deposit_price": "string",\
  "description": "string",\
  "duration_in_minutes": 0,\
  "id": "string",\
  "links": {\
    "self": "https://api.au1.cliniko.com/v1/appointment_types/1"\
  },\
  "max_attendees": 0,\
  "name": "string",\
  "online_bookings_lead_time_hours": 0,\
  "online_payments_enabled": true,\
  "online_payments_mode": "deposit_required",\
  "practitioners": {\
    "links": {\
      "self": "https://api.au1.cliniko.com/v1/practitioners?q%5B%5D=appointment_type_id%3A%3D1"\
    }\
  },\
  "product": {\
    "links": {\
      "self": "https://api.au1.cliniko.com/v1/products/1"\
    }\
  },\
  "show_in_online_bookings": true,\
  "telehealth_enabled": true,\
  "treatment_note_template": {\
    "links": {\
      "self": "https://api.au1.cliniko.com/v1/treatment_note_templates/1"\
    }\
  },\
  "updated_at": "2019-08-24T14:15:22Z"\
}\
```\
\
## [link to Archive appointment type](https://docs.api.cliniko.com/openapi/appointment-type/archiveappointmenttype-post) Archive appointment type\
\
#### [link to /appointment-type/archiveappointmenttype-post\#appointment-type/archiveappointmenttype-post/request](https://docs.api.cliniko.com/openapi/appointment-type/archiveappointmenttype-post\#appointment-type/archiveappointmenttype-post/request) Request\
\
Security:\
\
basicAuth\
\
\
\
[link to /appointment-type/archiveappointmenttype-post#appointment-type/archiveappointmenttype-post/request/path](https://docs.api.cliniko.com/openapi/appointment-type/archiveappointmenttype-post#appointment-type/archiveappointmenttype-post/request/path) Path\
\
[link to /appointment-type/archiveappointmenttype-post#appointment-type/archiveappointmenttype-post/t=request&in=path&path=id](https://docs.api.cliniko.com/openapi/appointment-type/archiveappointmenttype-post#appointment-type/archiveappointmenttype-post/t=request&in=path&path=id) id _string_ _(int64)_ required\
\
post\
\
/appointment\_types/{id}/archive\
\
- Productionhttps://api.au1.cliniko.com/v1/appointment\_types/{id}/archive\
\
\
curl\
\
- curl\
- JavaScript\
- Python\
- Ruby\
\
```\
curl -i -X POST \\
  -u <username>:<password> \\
  'https://api.au1.cliniko.com/v1/appointment_types/{id}/archive'\
```\
\
#### [link to /appointment-type/archiveappointmenttype-post\#appointment-type/archiveappointmenttype-post/response&c=204](https://docs.api.cliniko.com/openapi/appointment-type/archiveappointmenttype-post\#appointment-type/archiveappointmenttype-post/response&c=204) Responses\
\
1. 204\
\
Resource was archived\
\
## [link to List appointment types for practitioner](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypesforpractitioner-get) List appointment types for practitioner\
\
#### [link to /appointment-type/listappointmenttypesforpractitioner-get\#appointment-type/listappointmenttypesforpractitioner-get/request](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypesforpractitioner-get\#appointment-type/listappointmenttypesforpractitioner-get/request) Request\
\
Security:\
\
basicAuth\
\
\
\
[link to /appointment-type/listappointmenttypesforpractitioner-get#appointment-type/listappointmenttypesforpractitioner-get/request/path](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypesforpractitioner-get#appointment-type/listappointmenttypesforpractitioner-get/request/path) Path\
\
[link to /appointment-type/listappointmenttypesforpractitioner-get#appointment-type/listappointmenttypesforpractitioner-get/t=request&in=path&path=practitioner_id](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypesforpractitioner-get#appointment-type/listappointmenttypesforpractitioner-get/t=request&in=path&path=practitioner_id) practitioner\_id _string_ _(int64)_ required\
\
[link to /appointment-type/listappointmenttypesforpractitioner-get#appointment-type/listappointmenttypesforpractitioner-get/request/query](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypesforpractitioner-get#appointment-type/listappointmenttypesforpractitioner-get/request/query) Query\
\
[link to /appointment-type/listappointmenttypesforpractitioner-get#appointment-type/listappointmenttypesforpractitioner-get/t=request&in=query&path=page](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypesforpractitioner-get#appointment-type/listappointmenttypesforpractitioner-get/t=request&in=query&path=page) page _integer_\
\
[link to /appointment-type/listappointmenttypesforpractitioner-get#appointment-type/listappointmenttypesforpractitioner-get/t=request&in=query&path=per_page](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypesforpractitioner-get#appointment-type/listappointmenttypesforpractitioner-get/t=request&in=query&path=per_page) per\_page _integer_ _\[ 1 .. 100 \]_\
\
[link to /appointment-type/listappointmenttypesforpractitioner-get#appointment-type/listappointmenttypesforpractitioner-get/t=request&in=query&path=sort](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypesforpractitioner-get#appointment-type/listappointmenttypesforpractitioner-get/t=request&in=query&path=sort) sort _Array of strings_\
\
Comma separated search fields. See: [Ordering](https://docs.api.cliniko.com/#ordering)\
\
Example:sort=created\_at:desc\
\
[link to /appointment-type/listappointmenttypesforpractitioner-get#appointment-type/listappointmenttypesforpractitioner-get/t=request&in=query&path=q[]](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypesforpractitioner-get#appointment-type/listappointmenttypesforpractitioner-get/t=request&in=query&path=q[]) q\[\] _Array of strings_\
\
Filter result by one or more fields.\
\
See [Filtering Results](https://docs.api.cliniko.com/#filtering-results)\
\
Available filters:\
\
| Value | Format |\
| --- | --- |\
| appointment\_confirmation\_template\_ids | [array](https://docs.api.cliniko.com/#array-filter-operators) |\
| appointment\_reminder\_template\_ids | [array](https://docs.api.cliniko.com/#array-filter-operators) |\
| archived\_at | [date-time](https://docs.api.cliniko.com/#datetime-filter-operators) |\
| category | [string](https://docs.api.cliniko.com/#string-filter-operators) |\
| created\_at | [date-time](https://docs.api.cliniko.com/#datetime-filter-operators) |\
| id | [int64](https://docs.api.cliniko.com/#numeric-filter-operators) |\
| online\_payments\_mode | [string](https://docs.api.cliniko.com/#string-filter-operators) |\
| show\_in\_online\_bookings | [boolean](https://docs.api.cliniko.com/#boolean-filter-operators) |\
| updated\_at | [date-time](https://docs.api.cliniko.com/#datetime-filter-operators) |\
\
[link to /appointment-type/listappointmenttypesforpractitioner-get#appointment-type/listappointmenttypesforpractitioner-get/t=request&in=query&path=order](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypesforpractitioner-get#appointment-type/listappointmenttypesforpractitioner-get/t=request&in=query&path=order) order _string_ Deprecated\
\
Enum"asc""desc"\
\
get\
\
/practitioners/{practitioner\_id}/appointment\_types\
\
- Productionhttps://api.au1.cliniko.com/v1/practitioners/{practitioner\_id}/appointment\_types\
\
\
curl\
\
- curl\
- JavaScript\
- Python\
- Ruby\
\
```\
curl -i -X GET \\
  -u <username>:<password> \\
  'https://api.au1.cliniko.com/v1/practitioners/{practitioner_id}/appointment_types?order=asc&page=0&per_page=1&q%5B%5D=string&sort=created_at%3Adesc'\
```\
\
#### [link to /appointment-type/listappointmenttypesforpractitioner-get\#appointment-type/listappointmenttypesforpractitioner-get/response&c=200](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypesforpractitioner-get\#appointment-type/listappointmenttypesforpractitioner-get/response&c=200) Responses\
\
1. 200\
\
Expand all\
\
successful operation\
\
[link to /appointment-type/listappointmenttypesforpractitioner-get#appointment-type/listappointmenttypesforpractitioner-get/response&c=200/body](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypesforpractitioner-get#appointment-type/listappointmenttypesforpractitioner-get/response&c=200/body) Bodyapplication/json\
\
[link to /appointment-type/listappointmenttypesforpractitioner-get#appointment-type/listappointmenttypesforpractitioner-get/t=response&c=200&path=appointment_types](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypesforpractitioner-get#appointment-type/listappointmenttypesforpractitioner-get/t=response&c=200&path=appointment_types) appointment\_types _Array of objects_ _(AppointmentType)_\
\
+Show 26 array properties\
\
[link to /appointment-type/listappointmenttypesforpractitioner-get#appointment-type/listappointmenttypesforpractitioner-get/t=response&c=200&path=total_entries](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypesforpractitioner-get#appointment-type/listappointmenttypesforpractitioner-get/t=response&c=200&path=total_entries) total\_entries _integer_\
\
Example:1\
\
[link to /appointment-type/listappointmenttypesforpractitioner-get#appointment-type/listappointmenttypesforpractitioner-get/t=response&c=200&path=links](https://docs.api.cliniko.com/openapi/appointment-type/listappointmenttypesforpractitioner-get#appointment-type/listappointmenttypesforpractitioner-get/t=response&c=200&path=links) links _object_\
\
+Show 3 properties\
\
Response\
\
1. 200\
\
application/json\
\
```\
\
{\
  "appointment_types": [\
    {\
      "add_deposit_to_account_credit": true,\
      "appointment_confirmation_template_ids": [\
        "1"\
      ],\
      "appointment_reminder_template_ids": [\
        "1"\
      ],\
      "appointment_type_billable_items": {\
        "links": { … }\
      },\
      "appointment_type_products": {\
        "links": { … }\
      },\
      "archived_at": "2019-08-24T14:15:22Z",\
      "billable_item": {\
        "links": { … }\
      },\
      "category": "string",\
      "color": "string",\
      "created_at": "2019-08-24T14:15:22Z",\
      "deposit_price": "string",\
      "description": "string",\
      "duration_in_minutes": 0,\
      "id": "string",\
      "links": {\
        "self": "https://api.au1.cliniko.com/v1/appointment_types/1"\
      },\
      "max_attendees": 0,\
      "name": "string",\
      "online_bookings_lead_time_hours": 0,\
      "online_payments_enabled": true,\
      "online_payments_mode": "deposit_required",\
      "practitioners": {\
        "links": { … }\
      },\
      "product": {\
        "links": { … }\
      },\
      "show_in_online_bookings": true,\
      "telehealth_enabled": true,\
      "treatment_note_template": {\
        "links": { … }\
      },\
      "updated_at": "2019-08-24T14:15:22Z"\
    }\
  ],\
  "total_entries": 1,\
  "links": {\
    "self": "https://api.au1.cliniko.com/v1/practitioners/1/appointment_types?page=2",\
    "previous": "https://api.au1.cliniko.com/v1/practitioners/1/appointment_types?page=1",\
    "next": "https://api.au1.cliniko.com/v1/practitioners/1/appointment_types?page=3"\
  }\
}\
```\
\
## [link to Archive appointment type](https://docs.api.cliniko.com/openapi/appointment-type/deleteappointmenttype-delete) Archive appointment typeDeprecated\
\
#### [link to /appointment-type/deleteappointmenttype-delete\#appointment-type/deleteappointmenttype-delete/request](https://docs.api.cliniko.com/openapi/appointment-type/deleteappointmenttype-delete\#appointment-type/deleteappointmenttype-delete/request) Request\
\
Security:\
\
basicAuth\
\
\
\
[link to /appointment-type/deleteappointmenttype-delete#appointment-type/deleteappointmenttype-delete/request/path](https://docs.api.cliniko.com/openapi/appointment-type/deleteappointmenttype-delete#appointment-type/deleteappointmenttype-delete/request/path) Path\
\
[link to /appointment-type/deleteappointmenttype-delete#appointment-type/deleteappointmenttype-delete/t=request&in=path&path=id](https://docs.api.cliniko.com/openapi/appointment-type/deleteappointmenttype-delete#appointment-type/deleteappointmenttype-delete/t=request&in=path&path=id) id _string_ _(int64)_ required\
\
delete\
\
/appointment\_types/{id}\
\
- Productionhttps://api.au1.cliniko.com/v1/appointment\_types/{id}\
\
\
curl\
\
- curl\
- JavaScript\
- Python\
- Ruby\
\
```\
curl -i -X DELETE \\
  -u <username>:<password> \\
  'https://api.au1.cliniko.com/v1/appointment_types/{id}'\
```\
\
#### [link to /appointment-type/deleteappointmenttype-delete\#appointment-type/deleteappointmenttype-delete/response&c=204](https://docs.api.cliniko.com/openapi/appointment-type/deleteappointmenttype-delete\#appointment-type/deleteappointmenttype-delete/response&c=204) Responses\
\
1. 204\
\
Resource was archived successfully\
\
## [link to Appointment Type Billable Item](https://docs.api.cliniko.com/openapi/appointment-type-billable-item) Appointment Type Billable Item\
\
Operations\
\
get\
\
/appointment\_type\_billable\_items\
\
post\
\
/appointment\_type\_billable\_items\
\
get\
\
/appointment\_type\_billable\_items/{id}\
\
patch\
\
/appointment\_type\_billable\_items/{id}\
\
delete\
\
/appointment\_type\_billable\_items/{id}\
\
\+ Show\
\
## [link to Appointment Type Product](https://docs.api.cliniko.com/openapi/appointment-type-product) Appointment Type Product\
\
Operations\
\
get\
\
/appointment\_type\_products\
\
post\
\
/appointment\_type\_products\
\
get\
\
/appointment\_type\_products/{id}\
\
patch\
\
/appointment\_type\_products/{id}\
\
delete\
\
/appointment\_type\_products/{id}\
\
\+ Show\
\
## [link to Attendee](https://docs.api.cliniko.com/openapi/attendee) Attendee\
\
Operations\
\
get\
\
/attendees\
\
post\
\
/attendees\
\
get\
\
/attendees/{id}\
\
patch\
\
/attendees/{id}\
\
post\
\
/attendees/{id}/archive\
\
patch\
\
/attendees/{id}/cancel\
\
delete\
\
/attendees/{id}Deprecated\
\
get\
\
/group\_appointments/{group\_appointment\_id}/attendeesDeprecatedShow2more...\
\
\+ Show\
\
## [link to Availability Block](https://docs.api.cliniko.com/openapi/availability-block) Availability Block\
\
Operations\
\
get\
\
/availability\_blocks\
\
post\
\
/availability\_blocks\
\
get\
\
/availability\_blocks/{id}\
\
\+ Show\
\
## [link to Available Time](https://docs.api.cliniko.com/openapi/available-time) Available Time\
\
Cliniko users can configure how available times are displayed in our online bookings module.\
\
The API endpoints that retrieve available times will respect these settings. The settings are:\
\
### Maximum number of appointments per day segment\
\
Day parts are morning (before Midday), afternoon (Midday to 5pm) and evening (5pm onwards).\
\
Possible settings are: 1, 2, 3, 4, 5 or unlimited.\
\
### Minimum advance time required for online bookings\
\
This is the minimum amount of time from now that a available time will be shown.\
\
Possible settings are: Now, 1 Hour, 2 Hours, 4 Hours, Tomorrow or 2 Days.\
\
### How far ahead bookings are offered\
\
This limits how far in the future available times are offered.\
\
Possible settings are: 28 days, 84 days, 182 days or 365 days\
\
### Business to be displayed in online bookings\
\
Setting to choose which businesses can be displayed in our online bookings module.\
\
The API will not return available times for businesses not enabled for online bookings.\
\
### Appointment Type to be displayed in online bookings\
\
Setting to choose which appointment types can be displayed in our online bookings module.\
\
The API will not return available times for appointment types not enabled for online bookings.\
\
### Practitioner to be displayed in online bookings\
\
Setting to choose which practitioners can be displayed in our online bookings module.\
\
The API will not return available times for practitioners not enabled for online bookings.\
\
Operations\
\
get\
\
/businesses/{business\_id}/practitioners/{practitioner\_id}/appointment\_types/{appointment\_type\_id}/available\_times\
\
get\
\
/businesses/{business\_id}/practitioners/{practitioner\_id}/appointment\_types/{appointment\_type\_id}/next\_available\_time\
\
\+ Show\
\
## [link to Billable Item](https://docs.api.cliniko.com/openapi/billable-item) Billable Item\
\
Operations\
\
get\
\
/billable\_items\
\
post\
\
/billable\_items\
\
get\
\
/billable\_items/{id}\
\
patch\
\
/billable\_items/{id}\
\
post\
\
/billable\_items/{id}/archive\
\
delete\
\
/billable\_items/{id}Deprecated\
\
\+ Show\
\
## [link to Booking](https://docs.api.cliniko.com/openapi/booking) Booking\
\
Operations\
\
get\
\
/bookings\
\
get\
\
/bookings/{id}\
\
get\
\
/patient\_cases/{patient\_case\_id}/bookingsDeprecated\
\
\+ Show\
\
## [link to Business](https://docs.api.cliniko.com/openapi/business) Business\
\
Businesses represent a business or location (e.g. a clinic). Each Cliniko account can have unlimited businesses.\
\
These are typically used for each physical location if there is more than one. Most Cliniko accounts have just onebusiness.\
\
Operations\
\
get\
\
/businesses\
\
post\
\
/businesses\
\
get\
\
/businesses/{id}\
\
patch\
\
/businesses/{id}\
\
post\
\
/businesses/{id}/archive\
\
post\
\
/businesses/{id}/unarchive\
\
delete\
\
/businesses/{id}Deprecated\
\
\+ Show\
\
## [link to Communication](https://docs.api.cliniko.com/openapi/communication) Communication\
\
Operations\
\
get\
\
/communications\
\
post\
\
/communications\
\
get\
\
/communications/{id}\
\
patch\
\
/communications/{id}\
\
post\
\
/communications/{id}/archive\
\
\+ Show\
\
## [link to Concession Price](https://docs.api.cliniko.com/openapi/concession-price) Concession Price\
\
Operations\
\
get\
\
/concession\_prices\
\
get\
\
/concession\_prices/{id}\
\
\+ Show\
\
## [link to Concession Type](https://docs.api.cliniko.com/openapi/concession-type) Concession Type\
\
Operations\
\
get\
\
/concession\_types\
\
post\
\
/concession\_types\
\
get\
\
/concession\_types/{id}\
\
patch\
\
/concession\_types/{id}\
\
\+ Show\
\
## [link to Contact](https://docs.api.cliniko.com/openapi/contact) Contact\
\
Operations\
\
get\
\
/contacts\
\
post\
\
/contacts\
\
get\
\
/contacts/{id}\
\
patch\
\
/contacts/{id}\
\
post\
\
/contacts/{id}/archive\
\
delete\
\
/contacts/{id}Deprecated\
\
\+ Show\
\
## [link to Daily Availability](https://docs.api.cliniko.com/openapi/daily-availability) Daily Availability\
\
The regularly scheduled availabilities of a practitioner at a business\
\
Operations\
\
get\
\
/daily\_availabilities\
\
get\
\
/daily\_availabilities/{id}\
\
get\
\
/businesses/{business\_id}/daily\_availabilities\
\
get\
\
/practitioners/{practitioner\_id}/daily\_availabilities\
\
\+ Show\
\
## [link to Group Appointment](https://docs.api.cliniko.com/openapi/group-appointment) Group Appointment\
\
Operations\
\
get\
\
/group\_appointments\
\
post\
\
/group\_appointments\
\
get\
\
/group\_appointments/{id}\
\
patch\
\
/group\_appointments/{id}\
\
post\
\
/group\_appointments/{id}/archive\
\
get\
\
/group\_appointments/{id}/conflicts\
\
delete\
\
/group\_appointments/{id}Deprecated\
\
\+ Show\
\
## [link to Individual Appointment](https://docs.api.cliniko.com/openapi/individual-appointment) Individual Appointment\
\
Operations\
\
get\
\
/individual\_appointments\
\
post\
\
/individual\_appointments\
\
get\
\
/individual\_appointments/{id}\
\
patch\
\
/individual\_appointments/{id}\
\
post\
\
/individual\_appointments/{id}/archive\
\
patch\
\
/individual\_appointments/{id}/cancel\
\
get\
\
/individual\_appointments/{id}/conflicts\
\
delete\
\
/individual\_appointments/{id}Deprecated\
\
\+ Show\
\
## [link to Invoice](https://docs.api.cliniko.com/openapi/invoice) Invoice\
\
Operations\
\
get\
\
/invoices\
\
get\
\
/invoices/{id}\
\
get\
\
/appointments/{appointment\_id}/invoices\
\
get\
\
/patient\_cases/{patient\_case\_id}/invoices\
\
get\
\
/attendees/{attendee\_id}/invoicesDeprecated\
\
get\
\
/patients/{patient\_id}/invoicesDeprecated\
\
get\
\
/practitioners/{practitioner\_id}/invoicesDeprecated\
\
\+ Show\
\
## [link to Invoice Item](https://docs.api.cliniko.com/openapi/invoice-item) Invoice Item\
\
Operations\
\
get\
\
/invoice\_items\
\
get\
\
/invoice\_items/{id}\
\
get\
\
/invoices/{invoice\_id}/invoice\_itemsDeprecated\
\
\+ Show\
\
## [link to Medical Alert](https://docs.api.cliniko.com/openapi/medical-alert) Medical Alert\
\
Operations\
\
get\
\
/medical\_alerts\
\
post\
\
/medical\_alerts\
\
get\
\
/medical\_alerts/{id}\
\
patch\
\
/medical\_alerts/{id}\
\
post\
\
/medical\_alerts/{id}/archive\
\
delete\
\
/medical\_alerts/{id}Deprecated\
\
get\
\
/patients/{patient\_id}/medical\_alertsDeprecated\
\
\+ Show\
\
## [link to Patient](https://docs.api.cliniko.com/openapi/patient) Patient\
\
Patients are the people that book in for appointments. There isn't much in Cliniko that doesn't revolve aroundpatients.\
\
When you're working with patient information, make sure you abide by the relevant regulations for security andprivacy.\
\
A couple of fields in the patient record deserve special consideration:\
\
`accepted_privacy_policy` stores the patient's consent to the business's own privacy policy. Values can be null(no response), true (accepted) or false (rejected). Please consider how this may affect you storing informationon this patient.\
\
`time_zone` will contain a valid IANA time zone identifier if the patient's time zone has been set, or null if ithasn't. It can be set via the API, in which case it accepts IANA time zone identifiers.\
\
Operations\
\
get\
\
/patients\
\
post\
\
/patients\
\
get\
\
/patients/{id}\
\
patch\
\
/patients/{id}\
\
post\
\
/patients/{id}/archive\
\
post\
\
/patients/{id}/unarchive\
\
delete\
\
/patients/{id}Deprecated\
\
\+ Show\
\
## [link to Patient Attachment](https://docs.api.cliniko.com/openapi/patient-attachment) Patient Attachment\
\
Operations\
\
get\
\
/patient\_attachments\
\
post\
\
/patient\_attachments\
\
get\
\
/patient\_attachments/{id}\
\
patch\
\
/patient\_attachments/{id}\
\
post\
\
/patient\_attachments/{id}/archive\
\
get\
\
/patient\_cases/{patient\_case\_id}/patient\_attachments\
\
get\
\
/patients/{patient\_id}/attachment\_presigned\_post\
\
delete\
\
/patient\_attachments/{id}DeprecatedShow1more...\
\
\+ Show\
\
## [link to Patient Case](https://docs.api.cliniko.com/openapi/patient-case) Patient Case\
\
Operations\
\
get\
\
/patient\_cases\
\
post\
\
/patient\_cases\
\
get\
\
/patient\_cases/active\
\
get\
\
/patient\_cases/{id}\
\
patch\
\
/patient\_cases/{id}\
\
post\
\
/patient\_cases/{id}/archive\
\
\+ Show\
\
## [link to Patient Form](https://docs.api.cliniko.com/openapi/patient-form) Patient Form\
\
HTML is supported in answers to paragraph questions. We sanitize these answers to ensure the HTML is safeand our editor can support the formatting.\
\
Currently, the following tags are supported: `p`, `div`, `br`, `ul`, `ol`, `li`, `blockquote`, `h1`, `h2`, `b`, `i`, `u`, and `a`.\
\
The angle bracket characters ( `<`, and `>`) should be sent as html encodings (ex: `<` should be sent as `&lt;`).\
\
Content inside unescaped angle brackets could be identified as unsupported HTML and will be stripped.\
\
Operations\
\
get\
\
/patient\_forms\
\
post\
\
/patient\_forms\
\
get\
\
/patient\_forms/{id}\
\
patch\
\
/patient\_forms/{id}\
\
post\
\
/patient\_forms/{id}/archive\
\
get\
\
/attendees/{attendee\_id}/patient\_formsDeprecated\
\
\+ Show\
\
## [link to Patient Form Template](https://docs.api.cliniko.com/openapi/patient-form-template) Patient Form Template\
\
Operations\
\
get\
\
/patient\_form\_templates\
\
post\
\
/patient\_form\_templates\
\
get\
\
/patient\_form\_templates/{id}\
\
patch\
\
/patient\_form\_templates/{id}\
\
post\
\
/patient\_form\_templates/{id}/archive\
\
\+ Show\
\
## [link to Practitioner](https://docs.api.cliniko.com/openapi/practitioner) Practitioner\
\
All practitioners have an associated user account. Not all users are practitioners (e.g. receptionists wouldn't be).\
\
You can only create appointments for practitioners (not for users).\
\
Operations\
\
get\
\
/practitioners\
\
get\
\
/practitioners/inactive\
\
get\
\
/practitioners/{id}\
\
get\
\
/appointment\_types/{appointment\_type\_id}/practitioners\
\
get\
\
/businesses/{business\_id}/practitioners\
\
get\
\
/appointment\_types/{appointment\_type\_id}/practitioners/inactive\
\
get\
\
/businesses/{business\_id}/practitioners/inactive\
\
\+ Show\
\
## [link to Practitioner Reference Number](https://docs.api.cliniko.com/openapi/practitioner-reference-number) Practitioner Reference Number\
\
Operations\
\
get\
\
/practitioner\_reference\_numbers\
\
post\
\
/practitioner\_reference\_numbers\
\
get\
\
/practitioner\_reference\_numbers/{id}\
\
patch\
\
/practitioner\_reference\_numbers/{id}\
\
delete\
\
/practitioner\_reference\_numbers/{id}\
\
get\
\
/practitioners/{practitioner\_id}/practitioner\_reference\_numbersDeprecated\
\
\+ Show\
\
## [link to Product](https://docs.api.cliniko.com/openapi/product) Product\
\
Operations\
\
get\
\
/products\
\
post\
\
/products\
\
get\
\
/products/{id}\
\
patch\
\
/products/{id}\
\
post\
\
/products/{id}/archive\
\
delete\
\
/products/{id}Deprecated\
\
\+ Show\
\
## [link to Product Supplier](https://docs.api.cliniko.com/openapi/product-supplier) Product Supplier\
\
Operations\
\
get\
\
/product\_suppliers\
\
post\
\
/product\_suppliers\
\
get\
\
/product\_suppliers/{id}\
\
patch\
\
/product\_suppliers/{id}\
\
post\
\
/product\_suppliers/{id}/archive\
\
delete\
\
/product\_suppliers/{id}Deprecated\
\
\+ Show\
\
## [link to Public Settings](https://docs.api.cliniko.com/openapi/public-settings) Public Settings\
\
Operations\
\
get\
\
/settings/public\
\
\+ Show\
\
## [link to Referral Source](https://docs.api.cliniko.com/openapi/referral-source) Referral Source\
\
Referral source of a patient\
\
Operations\
\
get\
\
/referral\_sources\
\
get\
\
/patients/{patient\_id}/referral\_source\
\
patch\
\
/patients/{patient\_id}/referral\_source\
\
\+ Show\
\
## [link to Referral Source Type](https://docs.api.cliniko.com/openapi/referral-source-type) Referral Source Type\
\
Types of referrals for patients\
\
Operations\
\
get\
\
/referral\_source\_types\
\
get\
\
/referral\_source\_types/{id}\
\
\+ Show\
\
## [link to Relationship](https://docs.api.cliniko.com/openapi/relationship) Relationship\
\
Operations\
\
get\
\
/relationships\
\
post\
\
/relationships\
\
get\
\
/relationships/{id}\
\
patch\
\
/relationships/{id}\
\
post\
\
/relationships/{id}/archive\
\
\+ Show\
\
## [link to Service](https://docs.api.cliniko.com/openapi/service) Service\
\
Operations\
\
get\
\
/services\
\
get\
\
/businesses/{business\_id}/services\
\
\+ Show\
\
## [link to Settings](https://docs.api.cliniko.com/openapi/settings) Settings\
\
Operations\
\
get\
\
/settings\
\
\+ Show\
\
## [link to Signature](https://docs.api.cliniko.com/openapi/signature) Signature\
\
Operations\
\
get\
\
/patient\_forms/{patient\_form\_id}/signatures/{id}\
\
\+ Show\
\
## [link to Stock Adjustment](https://docs.api.cliniko.com/openapi/stock-adjustment) Stock Adjustment\
\
Operations\
\
get\
\
/stock\_adjustments\
\
post\
\
/stock\_adjustments\
\
get\
\
/stock\_adjustments/{id}\
\
\+ Show\
\
## [link to Tax](https://docs.api.cliniko.com/openapi/tax) Tax\
\
Operations\
\
get\
\
/taxes\
\
post\
\
/taxes\
\
get\
\
/taxes/{id}\
\
patch\
\
/taxes/{id}\
\
delete\
\
/taxes/{id}\
\
\+ Show\
\
## [link to Treatment Note](https://docs.api.cliniko.com/openapi/treatment-note) Treatment Note\
\
Notes taken about a patient visit.\
\
HTML is supported in answers to paragraph questions. We sanitize these answers to ensure the HTML is safeand our editor can support the formatting.\
\
Currently, the following tags are supported: `p`, `div`, `br`, `ul`, `ol`, `li`, `blockquote`, `h1`, `h2`, `b`, `i`, `u`, and `a`.\
\
The angle bracket characters ( `<`, and `>`) should be sent as html encodings (ex: `<` should be sent as `&lt;`).\
\
Content inside unescaped angle brackets could be identified as unsupported HTML and will be stripped.\
\
Operations\
\
get\
\
/treatment\_notes\
\
post\
\
/treatment\_notes\
\
get\
\
/treatment\_notes/{id}\
\
patch\
\
/treatment\_notes/{id}\
\
get\
\
/patients/{patient\_id}/treatment\_notes\
\
post\
\
/treatment\_notes/{id}/archive\
\
post\
\
/treatment\_notes/{id}/unarchive\
\
delete\
\
/treatment\_notes/{id}Deprecated\
\
\+ Show\
\
## [link to Treatment Note Template](https://docs.api.cliniko.com/openapi/treatment-note-template) Treatment Note Template\
\
Templates that are the starting point for treatment notes.\
\
HTML is supported in answers to paragraph questions. We sanitize these answers to ensure the HTML is safeand our editor can support the formatting.\
\
Currently, the following tags are supported: `p`, `div`, `br`, `ul`, `ol`, `li`, `blockquote`, `h1`, `h2`, `b`, `i`, `u`, and `a`.\
\
The angle bracket characters ( `<`, and `>`) should be sent as html encodings (ex: `<` should be sent as `&lt;`).\
\
Content inside unescaped angle brackets could be identified as unsupported HTML and will be stripped.\
\
Operations\
\
get\
\
/treatment\_note\_templates\
\
post\
\
/treatment\_note\_templates\
\
get\
\
/treatment\_note\_templates/{id}\
\
patch\
\
/treatment\_note\_templates/{id}\
\
post\
\
/treatment\_note\_templates/{id}/archive\
\
delete\
\
/treatment\_note\_templates/{id}Deprecated\
\
\+ Show\
\
## [link to Unavailable Block](https://docs.api.cliniko.com/openapi/unavailable-block) Unavailable Block\
\
Operations\
\
get\
\
/unavailable\_blocks\
\
post\
\
/unavailable\_blocks\
\
get\
\
/unavailable\_blocks/{id}\
\
patch\
\
/unavailable\_blocks/{id}\
\
post\
\
/unavailable\_blocks/{id}/archive\
\
get\
\
/unavailable\_blocks/{id}/conflicts\
\
delete\
\
/unavailable\_blocks/{id}Deprecated\
\
\+ Show\
\
## [link to Unavailable Block Type](https://docs.api.cliniko.com/openapi/unavailable-block-type) Unavailable Block Type\
\
Operations\
\
get\
\
/unavailable\_block\_types\
\
post\
\
/unavailable\_block\_types\
\
get\
\
/unavailable\_block\_types/{id}\
\
patch\
\
/unavailable\_block\_types/{id}\
\
post\
\
/unavailable\_block\_types/{id}/archive\
\
\+ Show\
\
## [link to User](https://docs.api.cliniko.com/openapi/user) User\
\
Operations\
\
get\
\
/user\
\
get\
\
/users\
\
get\
\
/users/{id}\
\
\+ Show