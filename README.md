# etoro-cid

Resolve an eToro `cid` (Customer ID) to the account's public username.

## ما هو الـ cid؟ / What is `cid`?

الـ `cid` هو **Customer ID** — معرّف رقمي داخلي تستخدمه خوادم eToro وواجهات الـ API
لتمييز كل مستخدم أو محفظة بشكل فريد. روابط الملفات الشخصية العامة على المنصة تعتمد على
**اسم المستخدم** لا على الرقم، ولذلك لا تُفهرس أرقام الـ `cid` في محركات البحث ولا يمكن
الوصول إلى صاحب الحساب عبر بحث مباشر. الطريق العملي هو الاستعلام عن نقاط النهاية العامة
المفتاحها هو الـ `cid`.

`cid` is eToro's internal numeric **Customer ID** for a user/portfolio. Public
profile URLs are keyed by *username*, not by cid, so cids are not indexed by
search engines and a cid cannot be looked up directly. The practical route is to
query the public JSON endpoints that *are* keyed by cid.

## Usage

```
python3 etoro_cid.py 44260918
python3 etoro_cid.py 44260918 --raw        # full JSON payload
python3 etoro_cid.py 44260918 1234567      # several at once
```

Output:

```
44260918: SomeTrader  (via rankings)
  https://www.etoro.com/people/sometrader
```

No dependencies — Python 3.9+ standard library only.

## Endpoints queried

The script tries these in order and returns the first username it finds:

1. `sapi/trade-data-real/live/public/portfolios?format=json&cid=<cid>` — the
   public portfolio payload. Note this endpoint is primarily **positions** data;
   depending on the account and the current API shape it may not carry a
   username field at all.
2. `sapi/rankings/cid/<cid>/rankings/?Period=OneYearAgo` — the rankings payload,
   which backs the "popular investor" listings and carries the username more
   reliably.

Both are undocumented and their response shapes change without notice, so the
script walks the whole decoded JSON tree looking for any `*username*` key rather
than reading a fixed path.

## Caveats

- eToro fronts these endpoints with bot protection. A `403` or `429` usually
  means rate limiting or a blocked client, not a missing account. The script
  sends a browser `User-Agent` because the default Python one is rejected
  outright; beyond that, back off and retry rather than hammering.
- Only accounts with a **public** portfolio return data. Private accounts yield
  an empty or partial payload.
- This reads public profile data only. Nothing here authenticates or accesses
  anything private.

## Tests

```
python3 -m unittest discover -v
```

The tests cover the JSON-scanning logic, which runs without network access.
