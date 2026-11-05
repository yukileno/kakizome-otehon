// Run: node tools/test_layout.js
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname, "..");
const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
const script = html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
const sandbox = { window: { addEventListener() {} } };
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(root, "img/manifest.js"), "utf8"), sandbox);
vm.runInContext(script, sandbox);
const images = sandbox.window.GEN_IMAGES;
const layout = (word) => sandbox.layoutGenCharacters(word, images[word].segs, 1136, 4720);
for (const word of Object.keys(images)) {
  const glyphs = layout(word);
  assert.equal(glyphs.length, Array.from(word).length, word);
  for (const g of glyphs) {
    assert.ok(g.y >= -0.01 && g.y + g.h <= 4720.01, word);
    assert.ok(g.x >= -568.01 && g.x + g.w <= 568.01, word);
    assert.ok(g.w > 0 && g.h > 0, word);
  }
}
const [o, shi, yo, u] = layout("おしょうがつ");
assert.ok(yo.x > shi.x + shi.w, "small yo sits to the right of shi");
assert.ok(yo.y > shi.y, "small yo sits below shi");
assert.ok(yo.h < shi.h && yo.w < shi.w, "small kana stays small");
assert.ok(yo.y + yo.h < u.y, "small kana does not collide with the next row");
for (const word of ["あかるい", "青い空"]) {
  for (const g of layout(word)) assert.ok(Math.abs(g.x + g.w / 2) < 0.001, word);
}
console.log("PASS: 129 image layouts, kana centering and small-kana placement");
