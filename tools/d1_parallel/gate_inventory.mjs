// D1-D evidence inventory, not a security test or clinical release approval.
// Performs read-only scanning: it NEVER declares the patient runtime secure.
import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
function read(root,part){return fs.readFileSync(root+'/'+part,'utf8');}
export function inspect(root='.'){
 const db=read(root,'frontend/lib/data/drift/database.dart');
 const backups=read(root,'frontend/lib/data/drift/local_backup.dart');
 const controller=read(root,'frontend/lib/services/patient_vault_session_controller.dart');
 const start=db.indexOf('AppDatabase.forPatientVault(');
 const end=db.indexOf('/// Local row key',start);
 const ctor=start<0?'':db.slice(start,end<0?undefined:end);
 const findings={
  patientRuntimeUnkeyedDrift:ctor.includes("sqlite3Wasm: Uri.parse('sqlite3.wasm')")&&
      ctor.includes("driftWorker: Uri.parse('drift_worker.js')"),
  patientBackupPlainJson:backups.includes('static Future<String> exportVaultJson')&&
      backups.includes('return jsonEncode(envelope);'),
  sessionControllerUsesUnkeyedConstructor:controller.includes(
      '_openDatabase = openDatabase ?? AppDatabase.forPatientVault'),
  safariPhysicalEvidenceAbsentFromThisRepositoryScan:true,
  independentSecurityReviewAbsentFromThisRepositoryScan:true,
 };
 return {
  lot:'D1_WEB_NEW_VAULTS',
  patientRelease:'NO_GO',
  checkedAt:'source-snapshot-no-time-inference',
  description:'read-only known blockers; a passing inventory check is NOT a release approval',
  findings,
 };
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
 const report=inspect('.');
 fs.writeFileSync('d1-parallel-d-inventory.json',JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify(report,null,2));
}
