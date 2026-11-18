const fs = await import("node:fs/promises");
const task = await taskSpace("track-positioning");
const page = task.page("p1");
const vids = ["7696098742123131898","7507625720811769145","7694850607009616360","7690890266760252691","7696733191553551643","7696030453865647370","7677412771557805352","7696040163608251674","7696424009759542571","7696369600530746658"];
const out = [];
for (const v of vids) {
  try {
    await page.goto("https://www.douyin.com/video/"+v, {timeout:40000});
    await page.waitForTimeout(3000);
    const a = await page.evaluate(() => {
      const els = Array.from(document.querySelectorAll('a[href*="/user/MS4"]'));
      let best=null;
      for (const el of els) {
        let p = el;
        for (let i=0;i<5 && p;i++) {
          const tx = p.innerText || "";
          if (/粉丝\s*[\d.]+万?/.test(tx) && tx.length<200) { best={href:el.getAttribute("href"), txt:tx.replace(/\n/g," ")}; break; }
          p = p.parentElement;
        }
        if (best) break;
      }
      return best;
    });
    if (!a || !a.href) { out.push({vid:v, err:"no author"}); console.error("noauthor",v); continue; }
    const href = a.href.startsWith("//") ? "https:"+a.href : a.href;
    const clean = href.split("?")[0];
    await page.goto(clean, {timeout:40000});
    await page.waitForTimeout(3000);
    const p = await page.evaluate(() => {
      const t = document.body.innerText || "";
      const nameM = t.match(/登录\s*\n\s*([^\n]{2,24})\s*\n\s*关注/);
      const fansM = t.match(/粉丝\s*\n?\s*([\d.]+万?)/);
      const likeM = t.match(/获赞\s*\n?\s*([\d.]+万?)/);
      const wkM = t.match(/作品\s*\n?\s*(\d+)/);
      const bioM = t.match(/(抖音号：\d+)/);
      return {name:nameM&&nameM[1], fans:fansM&&fansM[1], like:likeM&&likeM[1], works:wkM&&wkM[1], dyid:bioM&&bioM[1], title:document.title, txt:t.slice(0,600).replace(/\n/g," | ")};
    });
    out.push({vid:v, url:clean, authorTxt:a.txt, ...p});
    console.error("ok", v, p.name, p.fans, p.works);
  } catch(e){ out.push({vid:v, err:String(e).slice(0,150)}); console.error("fail", v, String(e).slice(0,80)); }
}
await fs.writeFile("/Users/longyi/project/账号对标/00-战略与目标/track-positioning/work/tp_profiles.json", JSON.stringify(out,null,1));
console.log("done", out.length);
