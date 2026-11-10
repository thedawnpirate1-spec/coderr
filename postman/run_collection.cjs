// Minimal offline executor for the pm API subset used by this collection.
// For the full Postman runtime, import the collection into Postman or use Newman.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const { randomUUID } = require('node:crypto');
const readline = require('node:readline');

async function main() {
  const [file, base, output] = process.argv.slice(2);
  const collection = JSON.parse(fs.readFileSync(file, 'utf8'));
  const lines = readline.createInterface({input: process.stdin});
  async function fetch(url, options) {
    const reply = new Promise(resolve => lines.once('line', line => resolve(JSON.parse(line))));
    console.log('REQUEST ' + JSON.stringify({url, ...options}));
    const result = await reply;
    return {status: result.status, text: async () => result.body};
  }
  const variables = new Map(collection.variable.map(v => [v.key, v.value]));
  variables.set('base_url', base);
  const replace = value => value.replace(/\{\{([^}]+)\}\}/g, (_, key) =>
    key === '$guid' ? randomUUID() : variables.has(key) ? String(variables.get(key)) : (() => { throw Error(`Missing variable ${key}`); })());
  const stats = {requests: {total: 0, failed: 0}, assertions: {total: 0, failed: 0}};
  const failures = [];
  function expect(value) {
    const chain = {};
    for (const key of ['to', 'be', 'have', 'and', 'all']) Object.defineProperty(chain, key, {get: () => chain});
    chain.eql = expected => { assert.deepStrictEqual(value, expected); return chain; };
    chain.a = type => { assert.equal(typeof value, type); return chain; };
    chain.lengthOf = length => { assert.equal(value.length, length); return chain; };
    chain.keys = (...keys) => { assert.deepStrictEqual(Object.keys(value).sort(), keys.sort()); return chain; };
    Object.defineProperty(chain, 'not', {get: () => ({get empty() { assert.ok(value.length > 0); return chain; }})});
    return chain;
  }
  for (const item of collection.item) {
    const pm = {
      info: {requestName: item.name},
      collectionVariables: {get: key => variables.get(key), set: (key, value) => variables.set(key, value)},
      variables: {replaceIn: replace}, expect,
      test(name, fn) {
        stats.assertions.total++;
        try { fn(); } catch (error) {
          stats.assertions.failed++;
          failures.push({source: {name: item.name}, error: {message: `${name}: ${error.message}`}});
        }
      }
    };
    const run = event => vm.runInNewContext(event.script.exec.join('\n'), {pm}, {timeout: 1000});
    stats.requests.total++;
    try {
      for (const event of [...(collection.event || []), ...(item.event || [])]) if (event.listen === 'prerequest') run(event);
      const response = await fetch(replace(item.request.url), {
        method: item.request.method,
        headers: Object.fromEntries(item.request.header.map(h => [h.key, replace(h.value)])),
        body: item.request.body ? replace(item.request.body.raw) : undefined,
      });
      const body = await response.text();
      pm.response = {json: () => JSON.parse(body), to: {have: {status: expected => assert.equal(response.status, expected)}}};
      for (const event of item.event || []) if (event.listen === 'test') run(event);
      console.log(`${response.status} ${item.name}`);
    } catch (error) {
      stats.requests.failed++;
      failures.push({source: {name: item.name}, error: {message: error.message + (error.cause ? ': ' + error.cause.message : '')}});
    }
  }
  fs.writeFileSync(output, JSON.stringify({run: {stats, failures}}, null, 2));
  console.log(JSON.stringify({stats, failures}, null, 2));
  process.exitCode = failures.length ? 1 : 0;
  lines.close();
}
main().catch(error => { console.error(error.message); process.exitCode = 1; });
