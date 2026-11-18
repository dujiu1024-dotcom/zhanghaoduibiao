const fs = await import("node:fs/promises");
const task = await taskSpace("track-positioning");
const page = task.page("p1");
const qs = ["site%3Adouyin.com+%E7%A7%8B%E8%8A%9D2046", "site%3Adouyin.com+%E8%A3%85%E4%BF%AE%E6%97%A5%E8%AE%B0", "site%3Adouyin.com+%E5%88%9B%E4%B8%9A%E6%97%A5%E8%AE%B0"];
const out=[];
for (const q of qs){
  try{
    await page.goto("https://www.bing.com/search?q="+q+"&setlang=zh-CN", {timeout:40000});
    await page.waitForTimeout(2500);
    const r = await page.evaluate(()=>{
      const items = Array.from(document.querySelectorAll("li.b_algo")).slice(0,8).map(li=>{
        const a=li.querySelector("h2 a");
        return {t:a? (a.innerText||"").trim():"", h:a? a.href:""};
      });
      return {title:document.title, items};
    });
    out.push({q,...r}); console.error("ok",q);
  }catch(e){out.push({q,err:String(e).slice(0,120)}); console.error("fail",q);}
}
await fs.writeFile("/Users/longyi/project/账号对标/00-战略与目标/track-positioning/work/bing.json", JSON.stringify(out,null,1));
console.log("done");
