const fs = await import("node:fs/promises");
const task = await taskSpace("track-positioning");
const page = task.page("p1");
const urls = [
 "https://www.douyin.com/user/MS4wLjABAAAAwbbVuf1W2DdgRe0xCa0oxg1ZIHbzuiTzyjq3NcOVgBuu6qIidYlMYqbL3ZFY2swu",
 "https://www.douyin.com/user/MS4wLjABAAAAFAF86gZlOp2ef0VO1znxZJfr7QG8Yb5FufGtG9NOzJI",
 "https://www.douyin.com/user/MS4wLjABAAAAtXm4VPZs0y8kCSEDJqPzQfHWf-z_Y2nspM84Qbe9hQYjjpq_NjsBfd-ZKLX-Lbqu",
 "https://www.douyin.com/user/MS4wLjABAAAArf1tQOwb6SanMUp3DjcK00mdS6u4oX2-QYuMLAKDpjeKRQZYIxBFUy3vvZTRRzjI"
];
const out=[];
for (const u of urls){
  try{
    await page.goto(u,{timeout:40000});
    await page.waitForTimeout(3000);
    const p = await page.evaluate(()=>{
      const t=document.body.innerText||"";
      const g=(re)=>{const m=t.match(re);return m?m[1]:null;};
      return {title:document.title, name:g(/登录\s*\n\s*([^\n]{2,24})\s*\n\s*关注/), fans:g(/粉丝\s*\n?\s*([\d.]+万?)/), like:g(/获赞\s*\n?\s*([\d.]+万?)/), works:g(/作品\s*\n?\s*(\d+)/), dy:g(/(抖音号：[\w]+)/), block:t.slice(0,500).replace(/\n/g," | ")};
    });
    out.push({url:u,...p}); console.error("ok",p.name,p.fans,p.works);
  }catch(e){out.push({url:u,err:String(e).slice(0,120)});console.error("fail",u.slice(40));}
}
await fs.writeFile("/Users/longyi/project/账号对标/00-战略与目标/track-positioning/work/head_profiles.json", JSON.stringify(out,null,1));
console.log("done");
