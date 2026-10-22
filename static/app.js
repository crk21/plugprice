(function(){const R=window.ROOT||"";const S={E:"Available",T:"Temporarily unavailable",P:"Planned"};
const tf=document.getElementById("tf");if(tf){const rows=[...document.querySelectorAll("tbody tr")];tf.oninput=()=>{const q=tf.value.toLowerCase();rows.forEach(r=>r.style.display=r.textContent.toLowerCase().includes(q)?"":"none")}}
const res=document.getElementById("res");if(!res)return;let D=null;const esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const ids=["fs","fc","fn","fd"].map(i=>document.getElementById(i));
async function run(){const[s,c,n,d]=ids;if(!s.value&&!c.value&&!n.value&&!d.checked){res.innerHTML="<p>Pick a state, city or network.</p>";return}
if(!D){res.textContent="Loading…";D=await (await fetch(R+"data/stations.json")).json()}
const q=c.value.trim().toLowerCase();const m=D.filter(x=>(!s.value||x[3]==s.value)&&(!q||(x[2]||"").toLowerCase().includes(q))&&(!n.value||x[4]==n.value)&&(!d.checked||x[6]=="T"));
res.innerHTML=`<p>${m.length.toLocaleString()} stations${m.length>200?" (showing 200)":""}</p><div class="tw"><table><thead><tr><th>Station</th><th>Network</th><th>DC ports</th><th>Status</th><th>Price</th></tr></thead><tbody>`+m.slice(0,200).map(x=>`<tr><td><a href="${R}station/${x[0]}/index.html">${esc(x[1])}</a><br><small>${esc(x[2])}, ${x[3]}</small></td><td>${esc(x[4])}</td><td>${x[5]}</td><td><span class="b${x[6]}">${S[x[6]]||x[6]}</span></td><td>${x[7]?"$"+x[7].toFixed(2)+"/kWh":"—"}</td></tr>`).join("")+"</tbody></table></div>"}
ids.forEach(i=>i.addEventListener("input",run));run()})();
