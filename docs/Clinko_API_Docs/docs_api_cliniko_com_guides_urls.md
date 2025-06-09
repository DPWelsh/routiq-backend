Guides

/

Base URL and Shards

Last updated 3 months ago

## [link  to base-url--shards](https://docs.api.cliniko.com/guides/urls\#base-url--shards) Base URL & shards

All URLs in this documentation will use the following base, where `{shard}` is the Cliniko shard the account resides in.You can determine which shard to use through the Cliniko API key. API keys have the shard appended to the end, e.g. `MS0xLWl4SzYYYYdtR3V2HNOTAREALKEYwvNHdeW0pd-au2` is in the shard `au2`.If your API key was generated some time ago and has no shard on it, your shard will be `au1`.

```
https://api.{shard}.cliniko.com/v1

```

> Examples in this guide will typically use `au1` as the shard, unless the example requires otherwise. Please ensure you use **the appropriate** shard for your requests.

## [link  to current-regions-and-their-shards](https://docs.api.cliniko.com/guides/urls\#current-regions-and-their-shards) Current regions and their shards

| Region | Shard |
| --- | --- |
| AU | `au1` |
| AU | `au2` |
| AU | `au3` |
| AU | `au4` |
| CA | `ca1` |
| UK | `uk1` |
| UK | `uk2` |
| EU | `eu1` |

It is **strongly** advisable that you validate the shard component:

- being one of these shard values, or
- matches the regex `/\w{2}\d{1,2}/i`

For more about the introduction of shards, and a code example of API keys with the shard attached may be used, [read the guide](https://docs.api.cliniko.com/guides/sharding).

Previous page [Introduction](https://docs.api.cliniko.com/)

Next page [Sharding](https://docs.api.cliniko.com/guides/sharding)