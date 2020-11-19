# POC of caching with Django, Domain Driven Design, DataLoaders and GraphQL

This is a small POC for [Pollen](https://team.pollen.co/), we want to understand
what caching patterns we can introduce in our new GraphQL infrastructure. The
goal is to create optimised GraphQL queries without a lot of effort.

We also want to make sure that we can inspect requests and understand what's
happening, so we want to get visibility on the number of queries and cache hits
for example.

## Background/ideas

We are using domain driven design and our code structure looks like this:

```text
                                                                  +--------------+
                                                                  |              |
                                                          +-----> |   Database   |
+-----------------+              +----------------------+ |       |              |
|                 |              |                      | |       +--------------+
|  GraphQL Types  | +----------> |     Repositories     | +
|                 |              |                      | |
+-----------------+              +----------------------+ |       +--------------+
                                                          |       |              |
                                                          +-----> |    Redis     |
                                                                  |              |
                                                                  +--------------+
```

Our GraphQL Layer doesn't communicate directly with the storage layer, that's
all done in our domain layer using repositories and entities.

Repositories allow you do fetch and persist data. Entities represent data in the
domain (similar to a django model, but with less implementation details).

We want to do caching using Redis and single entities, so we never[1] cache
lists of data, only single entities by id.

The data would be stored in redis as JSON and the key would be: `Entity-ID`.
Related data should not be stored as part of one entity, instead store the id
and fetch it later when needed.

## GraphQL

GraphQL makes it easier to prototype new feature, but also makes it easier to
write queries that don't perform well, for example this query:

```graphql
{
  campaigns(first: 5) {
    id
    title
    events(first: 2) {
      id
      title
    }
  }
}
```

Easily results in n+1 queries, as you'd do the follow queries:

- 1 to fetch the first 5 campaigns
- 1 to fetch the first 2 events for each campaign

To be fair this is probably one of the worst kind of queries to optimise, since
we have pagination inside nested fields.

One idea would be to prevent this kind of queries, by either returning an error,
as it might make sense to fetch the first 2 events when fetching a single
campaign. Or we can move fetching the events as being a top level query,
preventing this query from ever happening.

## Current state

We worked on this query, to see what we can/should optimise and what we can't:

```graphql
{
  campaigns(first: 5) {
    id
    title
    events(first: 2) {
      id
      title
    }
  }
}
```

Right now this query suffers of the n+1 problem, but it only fetches ids from
the databases, the rest comes from Redis when possible, so it works like this:

- 1 query to fetch a list of campaign ids
- 1 query per campaign to fetch a list of event ids
- 1 redis get for each campaign (fallbacks to db) <- can be batched
- 1 redis get for each event (fallbacks to db) <- it is batched but not too much

## Base repository implementation

We now have a base repository called `BaseCacheRepository` that knows how store
and fetch single or multiple entities from redis. And it also knows how to fetch
a single entity from the db, so it would provide a public interface like this:

```python
class MyRepository(BaseCacheRepository):
    model_class = MyModel
    entity_class = MyEntity

repo = MyRepository()

a = repo.get_by_id("123")
```

[1] unless there's a really good use case for it
