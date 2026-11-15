const fs = await import("node:fs/promises");
const task = await taskSpace("track-positioning");
const page = task.page("p1");
const ids = ["7696092121946807482","7696823055703641387","7695856144631221542","7695941975057420137"];
const out = [];
for (const id of ids) {
  try {
    await page.goto("https://www.douyin.com/video/"+id, {timeout: 45000});
    await page.waitForTimeout(3500);
    const d = await page.evaluate(() => {
      const t = document.body.innerText || "";
      const i = t.indexOf("全部评论");
      return {title: document.title, cmt: i>0 ? t.slice(i, i+1200) : t.slice(0,1200)};
    });
    out.push({id, ...d});
    console.error("ok", id);
  } catch(e){ out.push({id, error:String(e).slice(0,120)}); console.error("fail", id); }
}
await fs.writeFile("/Users/longyi/project/账号对标/00-战略与目标/track-positioning/work/a_comments.json", JSON.stringify(out,null,1));
console.log("done");
