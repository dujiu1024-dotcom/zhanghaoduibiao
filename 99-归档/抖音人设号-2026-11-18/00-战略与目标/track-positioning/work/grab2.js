const fs = await import("node:fs/promises");
const task = await taskSpace("track-positioning");
const page = task.page("p1");
const targets = [
  ["C","7696098192979986468"],["C","7696277430436104192"],["C","7696366536281294884"],
  ["C","7696002953357822006"],["C","7696401771572234240"],["C","7696051880689928235"],
  ["C","7696506925369788458"],
  ["B","7696725121943209993"],["B","7696423748442572827"],
];
const out = [];
for (const [pool,id] of targets) {
  try {
    await page.goto("https://www.douyin.com/collection/"+id, {timeout: 45000});
    await page.waitForTimeout(3500);
    const d = await page.evaluate(() => {
      const txt = document.body.innerText || "";
      const authors = Array.from(document.querySelectorAll('a[href*="/user/MS4"]')).map(a=>({h:a.getAttribute("href"), t:(a.innerText||"").trim().slice(0,30)})).filter(x=>x.t);
      return {url: location.href, title: document.title, txt: txt.slice(0, 6000), authors: authors.slice(0,6)};
    });
    out.push({pool, id, ...d});
    console.error("ok", pool, id);
  } catch(e) { out.push({pool,id,error:String(e).slice(0,150)}); console.error("fail",id,String(e).slice(0,100)); }
}
await fs.writeFile("/Users/longyi/project/账号对标/00-战略与目标/track-positioning/work/bc_collections.json", JSON.stringify(out,null,1));
console.log("done", out.length);
