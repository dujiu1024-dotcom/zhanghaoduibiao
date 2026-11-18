const fs = await import("node:fs/promises");
const task = await taskSpace("track-positioning");
const page = task.page("p1");
const ids = ["7696029756219164722","7696033563199670323","7696104311096346634","7696039168606767140","7696368997297555466"];
const out = [];
for (const id of ids) {
  try {
    await page.goto("https://www.douyin.com/collection/"+id, {timeout: 45000});
    await page.waitForTimeout(3500);
    const d = await page.evaluate(() => {
      const txt = document.body.innerText || "";
      const anchors = Array.from(document.querySelectorAll('a[href*="/user/"]')).map(a=>({h:a.getAttribute("href"), t:(a.innerText||"").trim().slice(0,40)}));
      const seen = new Set(); const uniq = [];
      for (const a of anchors) { if(!seen.has(a.h)){seen.add(a.h); uniq.push(a);} }
      return {url: location.href, title: document.title, txt: txt.slice(0, 4000), anchors: uniq.slice(0,5)};
    });
    out.push({id, ...d});
    console.error("ok", id, d.title);
  } catch(e) {
    out.push({id, error: String(e).slice(0,200)});
    console.error("fail", id, String(e).slice(0,120));
  }
}
await fs.writeFile("/Users/longyi/project/账号对标/00-战略与目标/track-positioning/work/b_collections.json", JSON.stringify(out,null,1));
console.log("done", out.length);
