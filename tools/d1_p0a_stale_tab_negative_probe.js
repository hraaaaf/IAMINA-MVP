// IAMINA D1 P0-A (ported from D18 PR #1265): advisory Web Locks cannot fence pre-D18 open tabs.
// Synthetic IndexedDB only; PASS means old writers remain a clinical NO-GO.
'use strict';
const http = require('node:http');
const {chromium, webkit} = require('playwright');
const browserName=process.env.D18_STALE_BROWSER||'chromium';
if(!['chromium','webkit'].includes(browserName))throw Error('D18_BAD_BROWSER');
const root='iamina:d18:precutover:source:v1:';
const vault='amina_vault_v1_native_734';
const checks=[];
function check(name,actual,expected){
  const pass=actual===expected; checks.push({phase:name,pass});
  if(!pass)throw Error('D18_STALE_TAB_'+name);
}
const server=http.createServer((req,res)=>{
  res.writeHead(200,{'content-type':'text/html','cache-control':'no-store'});
  res.end('<!doctype html><title>D18 LEGACY NEGATIVE CI ONLY</title>');
});
// Separate feasibility experiment: IDB versionchange is a physical exclusive
// upgrade, unlike advisory Web Locks. THIS IS NOT the real Drift SQLite VFS:
// never use this synthetic store rename on a patient database.
async function runSyntheticVersionchangeFixture(ctx,url) {
  const physical='d18-ci-synthetic-version-fence';
  const legacy=await ctx.newPage(),upgrader=await ctx.newPage();
  try {
    await legacy.goto(url);await upgrader.goto(url);
    check('versioned_legacy_v1_seeded',await legacy.evaluate(async physical=>{
      const db=await new Promise((resolve,reject)=>{
        const req=indexedDB.open(physical,1);
        req.onupgradeneeded=()=>req.result.createObjectStore('rows');
        req.onsuccess=()=>resolve(req.result);
        req.onerror=()=>reject(req.error);
      });
      window.__oldVersionedDb=db;
      const tx=db.transaction('rows','readwrite');
      tx.objectStore('rows').put('SYNTHETIC_OLD',1);
      return new Promise((resolve,reject)=>{
        tx.oncomplete=()=>resolve(true);
        tx.onabort=()=>reject(tx.error);
        tx.onerror=()=>reject(tx.error);
      });
    },physical),true);

    await upgrader.evaluate(physical=>{
      window.__fence={blocked:false,upgraded:false,ready:false,error:null};
      const req=indexedDB.open(physical,2);
      req.onblocked=()=>{window.__fence.blocked=true;};
      req.onupgradeneeded=()=>{
        // Renaming is atomic with versionchange; preserve existing records.
        req.transaction.objectStore('rows').name='archived_rows_v1';
        window.__fence.upgraded=true;
      };
      req.onsuccess=()=>{window.__fence.db=req.result;window.__fence.ready=true;};
      req.onerror=()=>{window.__fence.error=req.error?.name||'UNKNOWN';};
    },physical);
    await upgrader.waitForFunction(()=>window.__fence.blocked===true,
      null,{timeout:15000});
    check('upgrade_blocked_by_unclean_old_handle',
      await upgrader.evaluate(()=>window.__fence.blocked &&
        !window.__fence.ready&&!window.__fence.upgraded),true);
    check('late_legacy_commit_before_upgrade',await legacy.evaluate(async()=>{
      const tx=window.__oldVersionedDb.transaction('rows','readwrite');
      tx.objectStore('rows').put('SYNTHETIC_BEFORE_FENCE',2);
      return new Promise((resolve,reject)=>{
        tx.oncomplete=()=>resolve(true);
        tx.onabort=()=>reject(tx.error);
        tx.onerror=()=>reject(tx.error);
      });
    }),true);

    // Do not upgrade or publish while old connection remains open.
    await legacy.evaluate(()=>window.__oldVersionedDb.close());
    await upgrader.waitForFunction(
      ()=>window.__fence.ready===true||window.__fence.error!==null,
      null,{timeout:15000});
    check('versionchange_renames_source_losslessly',
      await upgrader.evaluate(async()=>{
        const state=window.__fence,db=state.db;
        if(!state.upgraded||!state.ready||!db||
           db.objectStoreNames.contains('rows') ||
           !db.objectStoreNames.contains('archived_rows_v1'))return false;
        const tx=db.transaction('archived_rows_v1','readonly');
        const rows=await Promise.all([1,2].map(id=>new Promise((ok,bad)=>{
          const req=tx.objectStore('archived_rows_v1').get(id);
          req.onsuccess=()=>ok(req.result);
          req.onerror=()=>bad(req.error);
        })));
        return rows[0]==='SYNTHETIC_OLD' &&
          rows[1]==='SYNTHETIC_BEFORE_FENCE';
      }),true);

    check('version_pinned_v1_reopen_denied',
      await legacy.evaluate(physical=>new Promise(resolve=>{
        const req=indexedDB.open(physical,1);
        req.onerror=()=>resolve(req.error?.name==='VersionError');
        req.onsuccess=()=>{req.result.close();resolve(false);};
      }),physical),true);

    const oldUnversioned=()=>legacy.evaluate(physical=>new Promise(resolve=>{
      const req=indexedDB.open(physical);
      req.onerror=()=>resolve(false);
      req.onsuccess=()=>{
        const db=req.result;
        let denied=false;
        try{db.transaction('rows','readwrite');}
        catch(e){denied=e.name==='NotFoundError';}
        db.close();
        resolve(denied);
      };
    }),physical);
    check('unversioned_legacy_store_write_denied',await oldUnversioned(),true);
    await ctx.setOffline(true);
    check('offline_unversioned_store_write_denied',await oldUnversioned(),true);
    await ctx.setOffline(false);

    const reopened=await ctx.newPage();
    try {
      await reopened.goto(url);
      check('archive_remains_after_fresh_tab',
        await reopened.evaluate(async physical=>{
          const db=await new Promise((resolve,reject)=>{
            const req=indexedDB.open(physical,2);
            req.onsuccess=()=>resolve(req.result);
            req.onerror=()=>reject(req.error);
          });
          try{
            const tx=db.transaction('archived_rows_v1','readonly');
            const values=await Promise.all([1,2].map(i=>new Promise((ok,bad)=>{
              const req=tx.objectStore('archived_rows_v1').get(i);
              req.onsuccess=()=>ok(req.result);
              req.onerror=()=>bad(req.error);
            })));
            return values[0]==='SYNTHETIC_OLD' &&
              values[1]==='SYNTHETIC_BEFORE_FENCE';
          }finally{db.close();}
        },physical),true);
    } finally {await reopened.close();}
  } finally {
    await ctx.setOffline(false).catch(()=>{});
    await upgrader.close().catch(()=>{});
    await legacy.close().catch(()=>{});
  }
}

async function main(){
  await new Promise((resolve,reject)=>{
    server.once('error',reject);server.listen(0,'127.0.0.1',resolve);
  });
  let browser;
  try{
    browser=await (browserName==='chromium'?chromium:webkit).launch({
      headless:true,...(browserName==='chromium'?{args:['--no-sandbox']}:{})
    });
    const ctx=await browser.newContext({locale:'en-US'});
    const url='http://127.0.0.1:'+server.address().port+'/';
    const stale=await ctx.newPage();
    const migrator=await ctx.newPage();
    await stale.goto(url);await migrator.goto(url);
    // The stale bundle opened its physical storage BEFORE the new code.
    check('old_tab_does_not_load_bridge',
      await stale.evaluate(()=>!globalThis.IAMINA_D18_SOURCE_BARRIER),true);
    await stale.evaluate(async ()=>{
      window.__oldSource=await new Promise((resolve,reject)=>{
        const req=indexedDB.open('d18-legacy-synthetic-source',1);
        req.onupgradeneeded=()=>req.result.createObjectStore('rows');
        req.onsuccess=()=>resolve(req.result);
        req.onerror=()=>reject(req.error);
      });
    });
    await migrator.evaluate(({root,vault})=>{
      window.__hasBothLocks=false;
      const untilClosed=new Promise(resolve=>window.__releaseMigration=resolve);
      void navigator.locks.request(root+'legacy',{mode:'exclusive'},async legacy=>{
        if(!legacy)return;
        await navigator.locks.request(root+'patient:'+vault,
          {mode:'exclusive'},async patient=>{
            if(!patient)return;
            window.__hasBothLocks=true;
            await untilClosed;
          });
      });
    },{root,vault});
    await migrator.waitForFunction(()=>window.__hasBothLocks===true,null,{timeout:15000});
    const both=()=>migrator.evaluate(async ({root,vault})=>{
      const q=await navigator.locks.query();
      return [root+'legacy',root+'patient:'+vault].every(name=>
        q.held.some(l=>l.name===name&&l.mode==='exclusive'));
    },{root,vault});
    check('exclusive_locks_actually_held',await both(),true);
    check('cooperative_request_would_be_denied',
      await stale.evaluate(async root=>navigator.locks.request(
        root+'legacy',{mode:'shared',ifAvailable:true},lock=>lock===null),root),true);
    check('stale_tab_still_commits_to_source',
      await stale.evaluate(async ()=>{
        const tx=window.__oldSource.transaction('rows','readwrite');
        tx.objectStore('rows').put('SYNTHETIC_ONLY',734);
        return new Promise((resolve,reject)=>{
          tx.oncomplete=()=>resolve(true);
          tx.onerror=()=>reject(tx.error);
          tx.onabort=()=>reject(tx.error);
        });
      }),true);
    check('migrator_reads_new_record_despite_its_locks',
      await migrator.evaluate(async ()=>{
        const db=await new Promise((resolve,reject)=>{
          const r=indexedDB.open('d18-legacy-synthetic-source',1);
          r.onsuccess=()=>resolve(r.result);
          r.onerror=()=>reject(r.error);
        });
        try{
          const tx=db.transaction('rows','readonly');
          const copied = await new Promise((resolve,reject)=>{
            const r=tx.objectStore('rows').get(734);
            r.onsuccess=()=>resolve(r.result);
            r.onerror=()=>reject(r.error);
          });
          // Model only the captured logical source row; no ciphertext,
          // no clinical snapshot and no migration pointer is created.
          window.__candidateCopyBeforeStaleWrite=copied;
          return copied==='SYNTHETIC_ONLY';
        }finally{db.close();}
      }),true);
    // The original tab survives a candidate copy and can still change the
    // physical source without participating in any new Web Locks.
    check('legacy_write_after_candidate_copy_commits',
      await stale.evaluate(async ()=>{
        const tx=window.__oldSource.transaction('rows','readwrite');
        tx.objectStore('rows').put('SYNTHETIC_LATE_OFFLINE_WRITE',734);
        return new Promise((resolve,reject)=>{
          tx.oncomplete=()=>resolve(true);
          tx.onerror=()=>reject(tx.error);
          tx.onabort=()=>reject(tx.error);
        });
      }),true);
    check('candidate_copy_is_stale_while_locks_held',
      await migrator.evaluate(async ()=>{
        const db=await new Promise((resolve,reject)=>{
          const r=indexedDB.open('d18-legacy-synthetic-source',1);
          r.onsuccess=()=>resolve(r.result);
          r.onerror=()=>reject(r.error);
        });
        try{
          const tx=db.transaction('rows','readonly');
          const current=await new Promise((resolve,reject)=>{
            const r=tx.objectStore('rows').get(734);
            r.onsuccess=()=>resolve(r.result);
            r.onerror=()=>reject(r.error);
          });
          return window.__candidateCopyBeforeStaleWrite==='SYNTHETIC_ONLY' &&
              current==='SYNTHETIC_LATE_OFFLINE_WRITE' &&
              current!==window.__candidateCopyBeforeStaleWrite;
        }finally{db.close();}
      }),true);
    // A point-in-time recheck cannot prevent another legacy write later.
    check('locks_still_held_after_uncooperative_write',await both(),true);
    // Emulate REAL network loss; offline capability is not just a phase name.
    await ctx.setOffline(true);
    check('legacy_page_network_is_offline',
      await stale.evaluate(()=>navigator.onLine===false),true);
    check('exclusive_web_locks_still_held_offline',await both(),true);
    // A cached legacy bundle can close its connection and later reopen
    // without ever obtaining/acknowledging a Web Lock. This models resume.
    check('offline_legacy_reopens_and_commits_under_exclusive_locks',
      await stale.evaluate(async ()=>{
        window.__oldSource.close();
        window.__oldSource=await new Promise((resolve,reject)=>{
          const req=indexedDB.open('d18-legacy-synthetic-source',1);
          req.onsuccess=()=>resolve(req.result);
          req.onerror=()=>reject(req.error);
        });
        const tx=window.__oldSource.transaction('rows','readwrite');
        tx.objectStore('rows').put('SYNTHETIC_RESUMED_OFFLINE_WRITE',735);
        return new Promise((resolve,reject)=>{
          tx.oncomplete=()=>resolve(true);
          tx.onerror=()=>reject(tx.error);
          tx.onabort=()=>reject(tx.error);
        });
      }),true);
    // Even a fresh source recheck is not a future-write exclusion proof.
    check('fresh_recheck_sees_resumed_write',
      await migrator.evaluate(async ()=>{
        const db=await new Promise((resolve,reject)=>{
          const r=indexedDB.open('d18-legacy-synthetic-source',1);
          r.onsuccess=()=>resolve(r.result);
          r.onerror=()=>reject(r.error);
        });
        try{
          const tx=db.transaction('rows','readonly');
          const row=await new Promise((resolve,reject)=>{
            const r=tx.objectStore('rows').get(735);
            r.onsuccess=()=>resolve(r.result);
            r.onerror=()=>reject(r.error);
          });
          return row==='SYNTHETIC_RESUMED_OFFLINE_WRITE';
        }finally{db.close();}
      }),true);
    // Restoring network connectivity still cannot retroactively fence an old
    // client; check a THIRD write after the migrator has re-read source.
    await ctx.setOffline(false);
    check('legacy_page_network_restored',
      await stale.evaluate(()=>navigator.onLine===true),true);
    check('third_legacy_write_after_fresh_recheck_commits',
      await stale.evaluate(async ()=>{
        const tx=window.__oldSource.transaction('rows','readwrite');
        tx.objectStore('rows').put('SYNTHETIC_AFTER_RECHECK',736);
        return new Promise((resolve,reject)=>{
          tx.oncomplete=()=>resolve(true);
          tx.onerror=()=>reject(tx.error);
          tx.onabort=()=>reject(tx.error);
        });
      }),true);
    check('exclusive_locks_still_cannot_fence_restarted_legacy_writer',
      await both(),true);
    // No cutover marker, deletion, pointer promotion or patient data touched.
    await migrator.evaluate(()=>window.__releaseMigration());
    await stale.evaluate(()=>window.__oldSource.close());
    check('legacy_source_intact_after_barrier_release',
      await migrator.evaluate(async ()=>{
        const db=await new Promise((resolve,reject)=>{
          const r=indexedDB.open('d18-legacy-synthetic-source',1);
          r.onsuccess=()=>resolve(r.result);
          r.onerror=()=>reject(r.error);
        });
        try{
          const tx=db.transaction('rows','readonly');
          const rows=await Promise.all([734,735,736].map(k=>
            new Promise((resolve,reject)=>{
              const r=tx.objectStore('rows').get(k);
              r.onsuccess=()=>resolve(r.result);
              r.onerror=()=>reject(r.error);
            })));
          return rows[0]==='SYNTHETIC_LATE_OFFLINE_WRITE' &&
            rows[1]==='SYNTHETIC_RESUMED_OFFLINE_WRITE' &&
            rows[2]==='SYNTHETIC_AFTER_RECHECK';
        }finally{db.close();}
      }),true);
    await runSyntheticVersionchangeFixture(ctx,url);
  }finally{
    await browser?.close().catch(()=>{});
    await new Promise(resolve=>server.close(resolve));
  }
}
(async()=>{
  try{await main();}
  catch(e){
    checks.push({phase:'harness',pass:false,code:String(e.message||'UNKNOWN')
      .replace(/[^A-Za-z0-9_]/g,'_').slice(0,110)});
    process.exitCode=1;
  }
  console.log(JSON.stringify({kind:'D18_STALE_TAB_BYPASS_NEGATIVE_NO_CUTOVER',
    engine:browserName,sha:process.env.GITHUB_SHA||null,checks}));
  if(checks.length!==24||checks.some(c=>!c.pass))process.exitCode=1;
})().catch(e=>{console.error('D18_STALE_TAB_FATAL',e.name);process.exitCode=1;});
