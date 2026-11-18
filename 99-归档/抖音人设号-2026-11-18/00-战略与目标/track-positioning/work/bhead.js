const fs = await import("node:fs/promises");
const task = await taskSpace("track-positioning");
const page = task.page("p1");
const qs = ["site%3Adouyin.com+%E7%A8%9A%E6%99%96%E5%90%9B","site%3Adouyin.com+%E7%A1%AC%E4%BB%B6%E8%8C%B6%E8%B0%88","site%3Adouyin.com+%E4%BD%95%E5%90%8C%E5%AD%A6","site%3Adouyin.com+%E5%A4%A7%E7%94%9C%E7%94%9C%E5%AE%B6%E7%9A%84%E8%A3%85%E4%BF%AE%E6%97%A5%E8%AE%B0"];
const res=[];
for (const q of qs){
  try{
    await page.goto("https://www.bing.com/search?q="+q+"&setlang=zh-CN",{timeout:40000});
    await page.waitForTimeout(2200);
    const r=await page.evaluate(()=>Array.from(document.querySelectorAll("li.b_algo h2 a")).slice(0,6).map(a=>({t:(a.innerText||"").trim(),h:a.href})));
    res.push({q,items:r}); console.error("ok",q);
  }catch(e){res.push({q,err:String(e).slice(0,100)});}
}
await fs.writeFile("/Users/longyi/project/账号对标/00-战略与目标/track-positioning/work/bhead_bing.json",JSON.stringify(res,null,1));
console.log(JSON.stringify(res.map(x=>({q:x.q, items:(x.items||[]).filter(i=>i.h.includes("/user/")).map(i=>i.h)})),null,1));
