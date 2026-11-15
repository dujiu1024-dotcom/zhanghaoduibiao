const fs = await import("node:fs/promises");
const task = await taskSpace("track-positioning");
const page = task.page("p1");
const urls = [
 "https://www.douyin.com/user/MS4wLjABAAAAoI6NbxoawvtqCOjNWePzwRoEIzGpM774sdUf0EuCkodHMSF1C3Px9pR94KgmEI87",
 "https://www.douyin.com/user/MS4wLjABAAAA6q-2hhkhT1G79dPjWl4kGfPBTWIPidx580dpW_QqmFxz7shWBtNzbV7W4Hga0KFb",
 "https://www.douyin.com/user/MS4wLjABAAAANVseRTg3-KjQZcwsgpToQ_oqA3kQtdO89wBPOSYqVMk",
 "https://www.douyin.com/user/MS4wLjABAAAA9w4v_PeLjkTRxSu56Tz_yokN9VEHmHLi1oawpFSqChJ0lVY4VHxLDqlsEhhuAJLX",
 "https://www.douyin.com/user/MS4wLjABAAAAjybI4idBpXque4OduMwgVPQt5ESJe0_TkAIQCMztViXv7DNOeI0947idizKvWT37",
 "https://www.douyin.com/user/MS4wLjABAAAArf1tQOwb6SanMUp3DjcK00mdS6u4oX2-QYuMLAKDpjeKRQZYIxBFUy3vvZTRRzjI"
];
const out=[];
for (const u of urls){
  try{
    await page.goto(u,{timeout:40000}); await page.waitForTimeout(2800);
    const p=await page.evaluate(()=>{
      const t=document.body.innerText||"";
      const g=(re)=>{const m=t.match(re);return m?m[1]:null;};
      const i=t.indexOf("作品"); 
      return {title:document.title, fans:g(/粉丝\s*\n?\s*([\d.]+万?)/), like:g(/获赞\s*\n?\s*([\d.]+万?)/), works:g(/作品\s*\n?\s*(\d+)/), dy:g(/(抖音号：[\w]+)/),
        head:t.slice(0,340).replace(/\n/g," | "), around:t.slice(Math.max(0,i-80), i+80).replace(/\n/g," | ")};
    });
    out.push({url:u,...p}); console.error("ok",p.title.slice(0,30),p.fans,p.works);
  }catch(e){out.push({url:u,err:String(e).slice(0,120)});console.error("fail",u.slice(40,70));}
}
await fs.writeFile("/Users/longyi/project/账号对标/00-战略与目标/track-positioning/work/head_profiles2.json",JSON.stringify(out,null,1));
console.log("done");
