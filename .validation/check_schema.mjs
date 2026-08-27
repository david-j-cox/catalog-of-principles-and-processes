// Guard against the failure that burned a whole calibration batch: a key listed in
// `required` but absent from `properties` while additionalProperties is false. No output
// can ever satisfy that, so every agent exhausts its retry cap and the run returns
// nothing after spending full price. Textual checks miss nested schemas, so this loads
// the real object and walks it.
//
// Usage: node .validation/check_schema.mjs <batch.mjs ...>   (exit 1 on a bad schema)
import { readFileSync } from 'node:fs'

function walk(node, path, problems) {
  if (!node || typeof node !== 'object') return
  if (Array.isArray(node)) return node.forEach((n, i) => walk(n, `${path}[${i}]`, problems))
  if (Array.isArray(node.required) && node.properties) {
    const props = new Set(Object.keys(node.properties))
    for (const r of node.required) {
      if (!props.has(r)) problems.push(`${path}: required '${r}' is not a declared property`)
    }
    if (node.additionalProperties === false) {
      for (const r of node.required) {
        if (!props.has(r)) problems.push(`${path}: '${r}' required but additionalProperties:false forbids it`)
      }
    }
  }
  for (const [k, v] of Object.entries(node)) walk(v, `${path}.${k}`, problems)
}

let bad = 0
for (const file of process.argv.slice(2)) {
  const src = readFileSync(file, 'utf8')
  const problems = []
  // pull every `const X_SCHEMA = { ... }` literal and evaluate just that object
  for (const m of src.matchAll(/const\s+(\w*SCHEMA\w*)\s*=\s*(\{)/g)) {
    let i = m.index + m[0].length - 1, depth = 0, end = -1
    for (let j = i; j < src.length; j++) {
      if (src[j] === '{') depth++
      else if (src[j] === '}' && --depth === 0) { end = j + 1; break }
    }
    if (end < 0) { problems.push(`${m[1]}: unbalanced braces`); continue }
    let obj
    try { obj = new Function(`return ${src.slice(i, end)}`)() }
    catch (e) { problems.push(`${m[1]}: not evaluable - ${e.message}`); continue }
    walk(obj, m[1], problems)
  }
  if (problems.length) { bad = 1; console.log(`FAIL ${file}`); problems.forEach(p => console.log('   ' + p)) }
  else console.log(`ok   ${file}`)
}
process.exit(bad)
